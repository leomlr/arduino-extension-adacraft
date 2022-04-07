class CLIENT:
  def __init__(self, port=80):
    self.station = None
    self.AP = None
    self.port = port
    self.servers_DB = {}
    self.server_ip = None

  def init(self, sta=None, ap=None):
    self.station = sta
    self.AP = ap

  def waitingServer(self, ip):
    import socket
    isConnected = False
    hadWaiting = False
    while not isConnected:
      try:
        server = socket.socket()
        server.connect((ip, self.port))
        self.server_ip = ip
        isConnected = True
        if hadWaiting:
          print('Connection Ok!')
        if self.AP is not None:
          ip_cl, mask, dns, gateway = self.AP.ifconfig()
        elif self.station is not None:
          ip_cl, mask, dns, gateway = self.station.ifconfig()
        else:
          raise ValueError("Station not connected or Access Point not started.")
        try:
          server.send('&&Connected client:&& ' + ip_cl)
          self.servers_DB[ip] = {
            'socket': server,
            'open': True,
            'send': [],
            'received': None
          }
        except OSError:
          print('Waiting server IP: {} PORT: {} ...\n'.format(ip, self.port))
          hadWaiting = True
          isConnected = False
      except OSError:
        print('Waiting server IP: {} PORT: {} ...\n'.format(ip, self.port))
        hadWaiting = True
        isConnected = False

  def manageSocket(self, ip):
    if self.station is not None and self.station.isconnected() or self.AP is not None:
      try:
        isServerOpen = self.servers_DB[ip]['open']
        if not isServerOpen:
          self.waitingServer(ip)
      except:
        self.waitingServer(ip)
    else:
      raise ValueError('Station not connected')

  def getServerData(self, ip):
    #print("getServerData...")
    if self.server_ip is None:
      self.manageSocket(ip)
    elif self.server_ip is not ip:
      self.clearBufferData()
      self.manageSocket(ip)
    return str(self.servers_DB[self.server_ip]['socket'].recv(1024))[2:-1]

  def sendDataToServer(self, data, ip, port=None):
    #print("sendDataToServer...")
    if port is not None:
      self.port = port
    if self.server_ip is None:
      self.manageSocket(ip)
    elif self.server_ip is not ip:
      self.clearBufferData()
      self.manageSocket(ip)
    self.servers_DB[self.server_ip]['socket'].send(data)

  def clearBufferData(self):
    #print("clearBufferData...")
    self.server_ip = None
    try:
      for ip in self.servers_DB:
        if self.servers_DB[ip]['open']:
          print("closing server connection: " + ip)
          self.servers_DB[ip]['received'] = None
          self.servers_DB[ip]['socket'].close()
          self.servers_DB[ip]['open'] = False
    except:pass
