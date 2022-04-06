import machine
class SERVER:
  def __init__(self):
    self.station = None
    self.AP = None
    self.client_ip = None
    self.server = None
    self.clients_DB = {}
    self.web_data_DB = {}
    self.html_page = None

  def start(self, sta=None, ap=None, ip='', port=80):
    self.AP = ap
    self.station = sta
    if self.server is None or (self.station is None and self.AP is not None):
      import socket
      self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      try:
        self.server.bind((ip, port))
        self.server.listen(50)
        if self.AP is not None:
          ip, mask, dns, gateway = self.AP.ifconfig()
        elif self.station is not None:
          ip, mask, dns, gateway = self.station.ifconfig()
        else:
          raise ValueError("Station not connected or Access Point not started.")
        print('Server started. IP: ' + ip)
      except OSError:
        machine.reset()

  def waitingClient(self):
    print("Waiting client...")
    client, address = self.server.accept()
    self.client_ip, port = address
    print("new client connection: " + str(self.client_ip))
    self.clients_DB[self.client_ip] = {
      'socket': client,
      'open': True,
      'send': [],
      'received': str(client.recv(1024))[2:-1],
      'html': False,
      'json': False,
    }

  def sendSocket(self, client, type, content):
    #print("sendSocket...")
    client.send('HTTP/1.1 200 OK\n')
    client.send('Content-Type: ' + content + '/' + type + '\n')
    client.send('Connection: close\n\n')
    if type is 'html':
      client.sendall(self.clients_DB[self.client_ip]['send'][0])
    else:
      client.send(self.clients_DB[self.client_ip]['send'][0])
    self.clients_DB[self.client_ip][type] = False
    client.close()
    self.clients_DB[self.client_ip]['open'] = False

  def manageSocket(self):
    #print("manageSocket...")
    if self.station is not None and self.station.isconnected() or self.AP is not None:
      try:
        cl = self.clients_DB[self.client_ip]['socket']
        if not self.clients_DB[self.client_ip]['open']:
          self.waitingClient()
      except KeyError:
        self.waitingClient()

  def getClientData(self):
    #print("getClientData...")
    if self.client_ip is None:
      self.manageSocket()
    if self.clients_DB[self.client_ip]['received'] is '&&Connected client:&& ' + self.client_ip:
      return None
    return self.clients_DB[self.client_ip]['received'].replace('&&Connected client:&& ' + self.client_ip, "")

  def getClientIp(self):
    #print("getClientIp...")
    if self.client_ip is None:
      self.manageSocket()
    return self.client_ip

  def sendDataToClient(self, data, html=False, json=False):
    #print("sendDataToClient...")
    if self.client_ip is None:
      self.manageSocket()
    self.clients_DB[self.client_ip]['html'] = html
    self.clients_DB[self.client_ip]['json'] = json
    self.clients_DB[self.client_ip]['send'].append(data)
    try:
      if self.clients_DB[self.client_ip]['open']:
        #print('NOT A NEW CLIENT IN DB: ' + self.client_ip)
        if self.clients_DB[self.client_ip]['received'] is None:
          #print('Data is None: ')
          client, address = self.server.accept()
          self.client_ip, port = address
          self.clients_DB[self.client_ip]['socket'] = client
          self.clients_DB[self.client_ip]['open'] = True
      cl = self.clients_DB[self.client_ip]['socket']
      dataToSend = self.clients_DB[self.client_ip]['send']
      if len(dataToSend) is not 0:
        if self.clients_DB[self.client_ip]['html']:
          self.sendSocket(cl, 'html', 'text')
        elif self.clients_DB[self.client_ip]['json']:
          self.sendSocket(cl, 'json', 'application')
        else:
          for i in range(len(dataToSend)):
            try: cl.send(dataToSend[i])
            except: print('Client disconnected')
        self.clients_DB[self.client_ip]['send'] = []
      if self.clients_DB[self.client_ip]['received'] is None or ('&&Connected client:&& ' + self.client_ip) in self.clients_DB[self.client_ip]['received']:
        self.clients_DB[self.client_ip]['received'] = str(cl.recv(1024))[2:-1]
    except KeyError:
      # print('NEW CLIENT In DB: ' + self.client_ip)
      self.waitingClient()

  def sendHtmlPage(self):
    self.sendDataToClient(self.html_page, html=True)

  def addCodeIntoHtml(self, fileName):
    try:
      f = open(fileName, 'r')
      script_code = f.read()
      if '.js' in fileName:
        if '<script>' in self.html_page:
          self.html_page = self.html_page.replace('</script>', script_code + '\n</script>')
        else:
          self.html_page = self.html_page.replace('</body>', '<script>\n' + script_code + '\n</script>\n</body>')
      elif '.css' in fileName:
        if '<style>' in self.html_page:
          self.html_page = self.html_page.replace('</style>', script_code + '\n</style>')
        else:
          self.html_page = self.html_page.replace('</head>', '<style>\n' + script_code + '\n</style>\n</head>')
      else:
        raise ValueError("File named '" + fileName + "' can't be added into HTML web page.")
      f.close()
    except IOError:
      raise IOError('No such file or directory ' + fileName)

  def updateDataWithRequest(self):
    data = self.getClientData().split(' HTTP')
    if data[0] and '=' in data[0] and not '/requestVariables&ip' in data[0]:
      data = data[0].split('GET /')[1].split('=')
      print(data)
      try:
        self.web_data_DB[self.client_ip][data[0]] = data[1]
      except KeyError:pass

  def getValueById(self, id, default=0, isBoolean=False):
    try:
      cl = self.web_data_DB[self.client_ip]
      try:
        value = self.web_data_DB[self.client_ip][id]
      except KeyError:
        self.web_data_DB[self.client_ip][id] = str(default)
    except KeyError:
      self.web_data_DB[self.client_ip] = {id: str(default)}
    if isBoolean:
      self.web_data_DB[self.client_ip][id] = "0"
    self.updateDataWithRequest()
    return self.web_data_DB[self.client_ip][id]

  def updateSwitchState(self, id):
    return "checked" if int(self.getValueById(id)) else ""

  def sendVariables(self, variables):
    request = self.getClientData()
    self.client_ip = self.getClientIp()
    request = request.split(' HTTP')[0]
    requestIp = request.split('&ip=')[1]
    if self.client_ip == requestIp:
      self.sendDataToClient(variables, json=True)

  def clearBufferData(self):
    self.client_ip = None
    try:
      for ip in self.clients_DB:
        print("closing client connection: " + ip)
        self.clients_DB[ip]['received'] = None
        self.clients_DB[ip]['socket'].close()
        self.clients_DB[ip]['open'] = False
      print("\n")
    except KeyError:pass
