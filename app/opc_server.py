import logging
import asyncio

from opcua import Server, ua
from datetime import datetime

from app.modbus_device import ModbusDevice

from typing import Dict
from app.conf import OPC_CONFIG, DEVICES


logger = logging.getLogger(__name__)

class OPCServer:
    """Класс OPC UA сервера"""
    
    def __init__(self):
        self.server = Server()
        self.devices: Dict[str, ModbusDevice] = {}
        self.opc_nodes = {}
        self.is_running = False
        
    async def setup_server(self):
        """Настройка OPC UA сервера"""
        logger.info("=== НАЧАЛО НАСТРОЙКИ OPC UA СЕРВЕРА ===")
        
        # Настройка сервера
        self.server.set_endpoint(OPC_CONFIG['endpoint'])
        self.server.set_server_name(OPC_CONFIG['server_name'])
        
        # Настройка пространства имен
        uri = OPC_CONFIG['uri']
        ns = self.server.register_namespace(uri)
        logger.info(f"Зарегистрировано пространство имен: {uri}, индекс: {ns}")
        
        # Получение корневого объекта
        objects = self.server.get_objects_node()
        logger.info("Получен корневой объект OPC UA")
        
        # Создание объектов для устройств
        logger.info(f"Количество устройств в конфигурации: {len(DEVICES)}")
        logger.info(f"Список устройств: {list(DEVICES.keys())}")
        
        for device_name, device_config in DEVICES.items():
            logger.info(f"=== СОЗДАНИЕ ОБЪЕКТА ДЛЯ УСТРОЙСТВА: {device_name} ===")
            logger.info(f"Конфигурация устройства {device_name}: порт {device_config['port']}, хост {device_config['host']}")
            
            try:
                # Создать объект устройства
                device_obj = objects.add_object(ns, device_name)
                logger.info(f"Создан объект устройства {device_name} в OPC UA")
                
                # Создать переменные для тегов
                self.opc_nodes[device_name] = {}
                logger.info(f"Количество тегов для {device_name}: {len(device_config['tags'])}")
                
                for tag_name, tag_config in device_config['tags'].items():
                    logger.info(f"  Создание тега: {device_name}.{tag_name}")
                    
                    # Определить тип данных
                    data_type_name = tag_config.get('data_type', 'float')
                    
                    # Создаем правильный NodeId для типа данных
                    if data_type_name == 'float':
                        data_type_node = ua.NodeId(ua.ObjectIds.Float)
                    elif data_type_name == 'int32':
                        data_type_node = ua.NodeId(ua.ObjectIds.Int32)
                    elif data_type_name == 'uint32':
                        data_type_node = ua.NodeId(ua.ObjectIds.UInt32)
                    elif data_type_name == 'int16':
                        data_type_node = ua.NodeId(ua.ObjectIds.Int16)
                    elif data_type_name == 'uint16':
                        data_type_node = ua.NodeId(ua.ObjectIds.UInt16)
                    elif data_type_name == 'bool':
                        data_type_node = ua.NodeId(ua.ObjectIds.Boolean)
                    else:
                        data_type_node = ua.NodeId(ua.ObjectIds.String)
                    
                    logger.info(f"    Тип данных: {data_type_name}")
                    
                    # Создать переменную с начальным значением и правильным типом
                    node = device_obj.add_variable(
                        ns, 
                        tag_name, 
                        0.0,  # начальное значение
                        datatype=data_type_node  # передаем NodeId
                    )
                    
                    # Сделать переменную доступной для записи
                    if tag_config.get('writable', True):
                        node.set_writable(True)
                        logger.info(f"    Тег {tag_name} доступен для записи")
                    
                    # Добавить описание (если есть)
                    if 'description' in tag_config:
                        logger.info(f"    Описание тега: {tag_config['description']} (пропущено)")
                    
                    self.opc_nodes[device_name][tag_name] = node
                    logger.info(f"  ✓ Тег {device_name}.{tag_name} успешно создан")
                
                logger.info(f"✓ Устройство {device_name} успешно добавлено в OPC UA")
                
            except Exception as e:
                logger.error(f"ОШИБКА при создании устройства {device_name}: {e}")
                continue
        
        # Проверка созданных устройств
        logger.info("=== ПРОВЕРКА СОЗДАННЫХ УСТРОЙСТВ ===")
        for device_name in DEVICES.keys():
            if device_name in self.opc_nodes:
                logger.info(f"✓ Устройство {device_name} добавлено в OPC UA, тегов: {len(self.opc_nodes[device_name])}")
                for tag_name in self.opc_nodes[device_name].keys():
                    logger.info(f"  - Тег: {device_name}.{tag_name}")
            else:
                logger.error(f"✗ Устройство {device_name} НЕ добавлено в OPC UA!")
        
        # ЗАПУСК СЕРВЕРА
        try:
            self.server.start()
            logger.info(f"OPC UA сервер запущен на {OPC_CONFIG['endpoint']}")
        except Exception as e:
            logger.error(f"Ошибка при запуске OPC UA сервера: {e}")
            raise
        
    async def start_devices(self):
        """Запуск подключения к устройствам"""
        logger.info("=== ЗАПУСК ПОДКЛЮЧЕНИЯ К УСТРОЙСТВАМ ===")
        
        for device_name, device_config in DEVICES.items():
            logger.info(f"Запуск устройства {device_name} на порту {device_config['port']}")
            device = ModbusDevice(device_name, device_config)
            self.devices[device_name] = device
            success = await device.connect()
            if success:
                logger.info(f"✓ Устройство {device_name} успешно подключено")
            else:
                logger.warning(f"⚠ Устройство {device_name} не подключено, будет попытка переподключения")
            
    async def update_values(self):
        """Обновление значений тегов"""
        update_count = 0
        while self.is_running:
            update_count += 1
            logger.info(f"=== ЦИКЛ ОБНОВЛЕНИЯ #{update_count} ===")
            
            for device_name in DEVICES.keys():
                if device_name not in self.devices:
                    logger.error(f"Устройство {device_name} не найдено в self.devices!")
                    device_config = DEVICES[device_name]
                    device = ModbusDevice(device_name, device_config)
                    self.devices[device_name] = device
                    await device.connect()
            
            for device_name, device_config in DEVICES.items():
                device = self.devices.get(device_name)
                
                if not device:
                    logger.error(f"Устройство {device_name} не найдено в списке устройств")
                    continue
                
                logger.info(f"Обработка устройства {device_name} (порт {device.config['port']})")
                
                # Если устройство не подключено - устанавливаем BAD для всех тегов
                if not device.is_connected:
                    logger.warning(f"Устройство {device_name} недоступно, попытка восстановить соединение...")
                    success = await device.reconnect()
                    if not success:
                        logger.error(f"Не удалось восстановить соединение с {device_name}")
                        # Устанавливаем качество BAD для всех тегов
                        for tag_name in device_config['tags']:
                            opc_node = self.opc_nodes.get(device_name, {}).get(tag_name)
                            if opc_node:
                                # Создаем DataValue с качеством BAD (без значения)
                                dv = ua.DataValue()
                                dv.StatusCode = ua.StatusCode(ua.StatusCodes.Bad)
                                dv.ServerTimestamp = datetime.now()
                                dv.SourceTimestamp = datetime.now()
                                opc_node.set_value(dv)
                                logger.debug(f"Тег {device_name}.{tag_name} установлен BAD")
                        continue
                
                all_tags_success = True
                for tag_name, tag_config in device_config['tags'].items():
                    try:
                        logger.debug(f"Чтение тега {device_name}.{tag_name}, адрес {tag_config['address']}")
                        
                        value = await device.read_register(
                            address=tag_config['address'],
                            count=tag_config.get('count', 1),
                            data_type=tag_config.get('data_type', 'float'),
                            scale=tag_config.get('scale', 1.0),
                            offset=tag_config.get('offset', 0.0),
                            byte_order=tag_config.get('byte_order', 'big'),
                            word_order=tag_config.get('word_order', 'big')
                        )
                        
                        opc_node = self.opc_nodes.get(device_name, {}).get(tag_name)
                        if opc_node:
                            if value is not None:
                                # Важно: используем правильный тип данных из тега
                                # Сначала определяем тип данных
                                data_type_name = tag_config.get('data_type', 'float')
                                
                                # Создаем Variant с правильным типом
                                if data_type_name == 'float':
                                    variant = ua.Variant(float(value), ua.VariantType.Float)
                                elif data_type_name == 'int32':
                                    variant = ua.Variant(int(value), ua.VariantType.Int32)
                                elif data_type_name == 'uint32':
                                    variant = ua.Variant(int(value), ua.VariantType.UInt32)
                                elif data_type_name == 'int16':
                                    variant = ua.Variant(int(value), ua.VariantType.Int16)
                                elif data_type_name == 'uint16':
                                    variant = ua.Variant(int(value), ua.VariantType.UInt16)
                                elif data_type_name == 'bool':
                                    variant = ua.Variant(bool(value), ua.VariantType.Boolean)
                                else:
                                    variant = ua.Variant(str(value), ua.VariantType.String)
                                
                                # Устанавливаем значение с качеством GOOD
                                dv = ua.DataValue(variant)
                                dv.ServerTimestamp = datetime.now()
                                dv.SourceTimestamp = datetime.now()
                                dv.StatusCode = ua.StatusCode(ua.StatusCodes.Good)
                                opc_node.set_value(dv)
                                logger.debug(f"Обновлен тег {device_name}.{tag_name} = {value} (GOOD)")
                            else:
                                # Устанавливаем качество BAD
                                dv = ua.DataValue()
                                dv.StatusCode = ua.StatusCode(ua.StatusCodes.Bad)
                                dv.ServerTimestamp = datetime.now()
                                dv.SourceTimestamp = datetime.now()
                                opc_node.set_value(dv)
                                all_tags_success = False
                                logger.warning(f"Тег {device_name}.{tag_name} установлен BAD (нет данных)")
                                
                    except Exception as e:
                        logger.error(f"Ошибка обновления {device_name}.{tag_name}: {e}")
                        all_tags_success = False
                        
                        # Устанавливаем качество BAD при ошибке
                        opc_node = self.opc_nodes.get(device_name, {}).get(tag_name)
                        if opc_node:
                            dv = ua.DataValue()
                            dv.StatusCode = ua.StatusCode(ua.StatusCodes.Bad)
                            dv.ServerTimestamp = datetime.now()
                            dv.SourceTimestamp = datetime.now()
                            opc_node.set_value(dv)
                            logger.warning(f"Тег {device_name}.{tag_name} установлен BAD (ошибка)")
                
                if device.is_connected and all_tags_success:
                    logger.info(f"✓ Устройство {device_name} (порт {device.config['port']}) опрошено успешно")
                elif device.is_connected:
                    logger.warning(f"⚠ Устройство {device_name} (порт {device.config['port']}) - частичные ошибки")
                else:
                    logger.error(f"✗ Устройство {device_name} (порт {device.config['port']}) недоступно")
            
            await asyncio.sleep(OPC_CONFIG['update_interval'])
            
    async def run(self):
        """Запуск сервера"""
        self.is_running = True
        
        try:
            await self.setup_server()
            await self.start_devices()
            
            logger.info(f"Запущен цикл обновления с интервалом {OPC_CONFIG['update_interval']} сек")
            
            await self.update_values()
            
        except Exception as e:
            logger.error(f"Ошибка сервера: {e}")
            self.is_running = False
            
    async def stop(self):
        """Остановка сервера"""
        logger.info("Остановка сервера...")
        self.is_running = False
        
        for device_name, device in self.devices.items():
            logger.info(f"Отключение устройства {device_name}")
            await device.disconnect()
        
        self.server.stop()
        logger.info("Сервер остановлен")
