import asyncio
import struct
import logging

from pymodbus.client import AsyncModbusTcpClient
from typing import Dict, Any, Optional


logger = logging.getLogger(__name__)

class ModbusDevice:
    """Класс для управления Modbus устройством"""
    
    def __init__(self, device_name: str, config: Dict[str, Any]):
        self.name = device_name
        self.config = config
        self.client: Optional[AsyncModbusTcpClient] = None
        self.is_connected = False
        self.last_error: Optional[str] = None
        self._lock = asyncio.Lock()
        
    async def connect(self) -> bool:
        """Подключение к Modbus устройству"""
        try:
            if self.client:
                try:
                    self.client.close()
                except:
                    pass
                self.client = None
            
            self.client = AsyncModbusTcpClient(
                host=self.config['host'],
                port=self.config['port'],
                framer=self.config.get('framer', 'rtu'),
                timeout=self.config.get('timeout', 1.0),
                retries=self.config.get('retries', 2)
            )
            
            await self.client.connect()
            self.is_connected = True
            self.last_error = None
            logger.info(f"Устройство {self.name} подключено: {self.config['host']}:{self.config['port']}")
            return True
            
        except Exception as e:
            self.is_connected = False
            self.last_error = str(e)
            logger.error(f"Ошибка подключения к устройству {self.name}: {e}")
            return False
    
    async def disconnect(self):
        """Отключение от Modbus устройства"""
        try:
            if self.client:
                self.client.close()
                self.client = None
            self.is_connected = False
            logger.info(f"Устройство {self.name} отключено")
        except Exception as e:
            logger.error(f"Ошибка при отключении устройства {self.name}: {e}")
    
    async def reconnect(self):
        """Попытка восстановить соединение"""
        await self.disconnect()
        await asyncio.sleep(2)
        return await self.connect()
    
    async def read_register(self, address: int, count: int, data_type: str, 
                           scale: float = 1.0, offset: float = 0.0,
                           byte_order: str = 'big', word_order: str = 'big') -> Optional[Any]:
        """Чтение регистра Modbus"""
        async with self._lock:
            if not self.is_connected:
                logger.warning(f"Устройство {self.name} не подключено")
                return None
            
            try:
                if count == 2:
                    result = await self.client.read_holding_registers(
                        address=address,
                        count=count,
                        device_id=self.config['device_id']
                    )
                    
                    if result.isError():
                        raise Exception(f"Ошибка чтения: {result}")
                    
                    if data_type == 'float':
                        value = self._registers_to_float(
                            result.registers, byte_order, word_order
                        )
                    elif data_type == 'int32':
                        value = self._registers_to_int32(
                            result.registers, byte_order, word_order
                        )
                    elif data_type == 'uint32':
                        value = self._registers_to_uint32(
                            result.registers, byte_order, word_order
                        )
                    else:
                        value = result.registers[0]
                        
                else:
                    result = await self.client.read_holding_registers(
                        address=address,
                        count=count,
                        device_id=self.config['device_id']
                    )
                    
                    if result.isError():
                        raise Exception(f"Ошибка чтения: {result}")
                    
                    if data_type in ['int16', 'uint16']:
                        value = result.registers[0]
                        if data_type == 'int16':
                            value = value if value < 32768 else value - 65536
                    else:
                        value = result.registers[0]
                
                value = value * scale + offset
                return value
                
            except Exception as e:
                self.last_error = str(e)
                self.is_connected = False
                logger.error(f"Ошибка чтения {self.name} адрес {address}: {e}")
                return None
    
    def _registers_to_float(self, registers, byte_order='big', word_order='big'):
        if len(registers) < 2:
            return 0.0
            
        if word_order == 'big':
            combined = (registers[0] << 16) | registers[1]
        else:
            combined = (registers[1] << 16) | registers[0]
            
        if byte_order == 'big':
            packed = struct.pack('>I', combined)
        else:
            packed = struct.pack('<I', combined)
            
        return struct.unpack('>f', packed)[0]
    
    def _registers_to_int32(self, registers, byte_order='big', word_order='big'):
        if len(registers) < 2:
            return 0
            
        if word_order == 'big':
            combined = (registers[0] << 16) | registers[1]
        else:
            combined = (registers[1] << 16) | registers[0]
            
        if combined >= 0x80000000:
            combined -= 0x100000000
            
        return combined
    
    def _registers_to_uint32(self, registers, byte_order='big', word_order='big'):
        if len(registers) < 2:
            return 0
            
        if word_order == 'big':
            return (registers[0] << 16) | registers[1]
        else:
            return (registers[1] << 16) | registers[0]
