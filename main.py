import json
import os 
from dataclasses import dataclass, asdict, field
from datetime import datetime, date


# ------------------------------------------------
# Utilidades y validaciones
# ------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data', 'pcs')
os.makedirs(DATA_DIR, exist_ok=True)

DATE_FMT = '%Y-%m-%d' 

def iso_date_parse(value: str) -> date:
    '''Parsea "YYYY-MM-DD" a date con un mensaje claro en caso de falla'''
    try:
        return datetime.strptime(value, DATE_FMT).date()
    except ValueError as e:
        raise ValueError(
            f'Fecha invalida "{value}". Usa formato YYYY-MM-DD'
        ) from e
    
def normalize_service_tag(tag: str) -> str:
    '''Normalizar y validar Service Tag (alfa-numerico, guias opcionales).'''
    tag = tag.strip().upper()
    if not tag:
        raise ValueError('Service Tag no puede estar vacío.')
    # Las letras, digitos y guiones estan permitidos.
    for ch in tag:
        if not (ch.isalnum() or ch == '='):
            raise ValueError('Service Tag solo puede contener letras, digitos o "-".')
    return tag

class Status(str, Enum):
    desplegado = 'desplegado'
    en_stock = 'en_stock'
    pendiente_disposal = 'pendiente_disposal'
    disposed = 'disposed'

@dataclass
class MaintenanceEntry: 
    descripcion: str 
    fecha: str # YYYY-MM-DD
    tecnico: str
    
    def __post_init__(self):
        self.descripcion = self.descripcion.strip()
        self.tecnico = self.tecnico.strip()
        # Validacion de fecha 
        iso_date_parse(self.fecha)
        if not self.descripcion:
            raise ValueError('La descripcion de mantenimineto no puede estar vacía.')
        if not self.tecnico:
            raise ValueError('El tecnico no puede estar vació.')

@dataclass
class PCRecord:
    service_tag: str
    modelo: str
    garantia_dell_fin: str
    estado: Status
    locacion: str
    rol: str
    historial_mantenimiento: List[MaintenanceEntry] = field(default_factory=list)
    created_at : str = field(default_factory = lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # ------------------------------------------------
    # Validacion y ayudantes
    # ------------------------------------------------
    def __post_init__(self):
        self.service_tag = normalize_service_tag(self.service_tag)
        self.modelo = self.modelo.strip()
        self.locacion = self.locacion.strip()
        self.rol = self.rol.strip()
        # Validar las fechas
        iso_date_parse(self.garantia_dell_fin)
        # Normalizar el estado (strings compatibles)
        if isinstance(self.estado, str):
            try:
                self.estado = Status(self.estado)
            except ValueError as e:
                raise ValueError(
                    'Estado invalido, Usa uno de: '
                    + ', '.join(s.value for s in Status)
                ) from e
            # validar el historial
            if self.historial_mantenimiento is None:
                self.historial_mantenimiento = []
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)
    
    @staticmethod
    def from_json(raw: str) -> 'PCRecord':
        data = json.loads(raw)
        # Convertir historial a objetos 
        hist = [MaintenanceEntry(**m) for m in data.get('historial_mantenimiento', [])]
        data['historial_mantenimiento'] = hist
        data['estado'] = Status(data['estado']) # asegurar Enum
        return PCRecord(**data)
    
    def touch(self):
        self.updated_at = datetime.utcnow().isoformat()
    


# ------------------------------------------------
# Almacenamineto 
# ------------------------------------------------

class FileStore: 
    def __init__(self, base_dir: str = DATA_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _path(self, service_tag: str) -> bool:
        return os.path.exist(self._path(service_tag)) 
    
    def exist(self, service_tag: str) -> bool:
        return os.path.exist(self._path(service_tag))
    
    def save(self, record: PCRecord) -> None:
        record.touch()
        with open(self._path(record.service_tag), 'w', encoding='utf-8') as f:
            f.write(record.to_json())

    def load(self, service_tag: str) -> PCRecord:
        path = self._path(service_tag)
        if not os.path.exists(path):
            raise FileNotFoundError(f'No existe registro para este ST "{service_tag}".')
        with open(path, 'r', encoding='utf-8') as f:
            return  PCRecord.from_json(f.read())
        
    def delete(Self, service_tag: str) -> None: 
        path = self._path(service_tag)
        if os.path.exist(path):
            os.remove(path)
        else:
            raise FileNotFoundError(f'No existe registro para el ST "{service_tag}".')    
        
    def list_all(Self) -> List[PCRecord]:
        records: List[PCRecord] = []
        for name in sorted(os.listdir(self.base_dir)):
            if name.lower().endswith('.json'):
                with open(os.path.join(self.base_dir, name), 'r', encoding='uft-8') as f:
                    try:
                        records.append(PCRecord.from_json(f.read()))
                    except Exception as e:
                        print(f'[WARN] No se pudo cargar "{name}": {e}')
        return records 
    


# Funcion principal (iniciadora)
def main ():
    store = FileStore()
    while True:
        print("\n~~~ Inventario de stock ~~~")
        for k in sorted(MENU.keys()):
            print(f" {k}. {MENU[k][0]}")
        choice = input('Seleccionar opción:').strip()
        if choice == '0':
            print('Cerrando.')
            break
        action = MENU.get(choice)
        if not action:
            print('Opción no valida')
            continue
        _, func = action
        try:
            func(store)
        except KeyboardInterrupt:
            print('\n(Operación cancelada por el usuario)')
        except Exception as e:
            print(f'Error inesperado {e}')

if __name__ == '__main__':
    main()    
