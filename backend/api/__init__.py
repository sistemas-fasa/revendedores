import pymysql

# Configurar pymysql para se comportar como mysqlclient
pymysql.install_as_MySQLdb()