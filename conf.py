# Конфигурация OPC UA сервера
OPC_CONFIG = {
    'endpoint': 'opc.tcp://127.0.0.1:54000/server/',
    'server_name': 'Simple Python Modbus OPC UA Server',
    'uri': 'http://example.com/myserver',  # Пространство имён
    'namespace': 'http://example.com/myserver',  # Альтернативное название
    'update_interval': 1.0,  # Интервал обновления данных в секундах
}

DEVICES = {
    'Dev01': {
        'tags': {
            'Temperature': {
                'address_type': 'holding_register',
                'address': 0,
                'count': 2,  # Для float нужно 2 регистра (32 бита)
                'scale': 1.0,
                'offset': 0.0,
                'writable': True,
                'data_type': 'uint16',
                'description': 'Температура в градусах Цельсия',
                'byte_order': 'big',      # или 'little'
                'word_order': 'big',      # порядок слов для float
            },
            'Pressure': {
                'address_type': 'holding_register',
                'address': 2,
                'count': 2,
                'scale': 0.1,
                'offset': 0.0,
                'writable': True,
                'data_type': 'float',
                'description': 'Давление в барах',
                'byte_order': 'big',      # или 'little'
                'word_order': 'big',      # порядок слов для float
            },
        },
        'host': '127.0.0.1',
        'port': 4001,
        'framer': 'rtu',  # rtu, socket, etc.
        'retries': 2,
        'device_id': 1,  # ID устройства Modbus (slave id)
        'timeout': 1.0,  # таймаут в секундах
        'device_survey': 1.0, # период опроса устройства
    },
    'Dev02': {
        'tags': {
            'Temperature2': {
                'address_type': 'holding_register',
                'address': 0,
                'count': 2,  # Для float нужно 2 регистра (32 бита)
                'scale': 1.0,
                'offset': 0.0,
                'writable': True,
                'data_type': 'uint16',
                'description': 'Температура в градусах Цельсия',
                'byte_order': 'big',      # или 'little'
                'word_order': 'big',      # порядок слов для float
            },
            'Pressure2': {
                'address_type': 'holding_register',
                'address': 2,
                'count': 2,
                'scale': 0.1,
                'offset': 0.0,
                'writable': True,
                'data_type': 'float',
                'description': 'Давление в барах',
                'byte_order': 'big',      # или 'little'
                'word_order': 'big',      # порядок слов для float
            },
        },
        'host': '127.0.0.1',
        'port': 4002,
        'framer': 'rtu',  # rtu, socket, etc.
        'retries': 2,
        'device_id': 1,  # ID устройства Modbus (slave id)
        'timeout': 1.0,  # таймаут в секундах
        'device_survey': 1.0, # период опроса устройства
    },
}

# Конфигурация тегов OPC с их соответствием Modbus адресам
# Формат: 
#   'имя_тега_OPC': {
#       'address_type': 'holding_register' | 'input_register' | 'coil' | 'discrete_input',
#       'address': int,  # Адрес в Modbus
#       'count': int,    # Количество регистров для чтения (для регистров)
#       'data_type': 'float' | 'int16' | 'uint16' | 'int32' | 'uint32' | 'bool',
#       'scale': float,  # Множитель для преобразования значения (опционально)
#       'offset': int,   # Смещение для преобразования значения (опционально)
#       'description': str,  # Описание тега (опционально)
#       'writable': bool,    # Можно ли записывать значение (опционально)
#   }