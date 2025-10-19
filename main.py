import json
import os 
from dataclasses import dataclass, asdict, field
from datetime import datetime, date, timezone
from enum import Enum
from typing import List, Optional


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
            f'Fecha invalida "{value}". Usa formato YYYY-MM-DD Ej. 2025-10-17'
        ) from e
    
def normalize_service_tag(tag: str) -> str:
    '''Normalizar y validar Service Tag (alfa-numerico, guias opcionales).'''
    tag = tag.strip().upper()
    if not tag:
        raise ValueError('Service Tag no puede estar vacío.')
    # Las letras, digitos y guiones estan permitidos.
    for ch in tag:
        if not (ch.isalnum() or ch == '-'):
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
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

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
        data = asdict(self)
        if isinstance(self.estado, Status):
            data["estado"] = self.estado.value
        return json.dumps(data, ensure_ascii=False, indent=2)

    def from_json(raw: str) -> 'PCRecord':
        data = json.loads(raw)
        # Convertir historial a objetos 
        hist = [MaintenanceEntry(**m) for m in data.get('historial_mantenimiento', [])]
        data['historial_mantenimiento'] = hist
        data['estado'] = Status(data['estado']) # asegurar Enum
        return PCRecord(**data)
    
    def touch(self):
        self.updated_at = datetime.now(timezone.utc).isoformat()
    


# ------------------------------------------------
# Almacenamineto 
# ------------------------------------------------

class FileStore: 
    def __init__(self, base_dir: str = DATA_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _path(self, service_tag: str) -> str:
        fname = f"{normalize_service_tag(service_tag)}.json"
        return os.path.join(self.base_dir, fname)
    
    def exists(self, service_tag: str) -> bool:
        return os.path.exists(self._path(service_tag))
    
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
        
    def delete(self, service_tag: str) -> None: 
        path = self._path(service_tag)
        if os.path.exists(path):
            os.remove(path)
        else:
            raise FileNotFoundError(f'No existe registro para el ST "{service_tag}".')    
        
    def list_all(self) -> List[PCRecord]:
        records: List[PCRecord] = []
        for name in sorted(os.listdir(self.base_dir)):
            if name.lower().endswith('.json'):
                with open(os.path.join(self.base_dir, name), 'r', encoding='utf-8') as f:
                    try:
                        records.append(PCRecord.from_json(f.read()))
                    except Exception as e:
                        print(f'[WARN] No se pudo cargar "{name}": {e}')
        return records 
    
# ------------------------------------------------
# UI de consola 
# ------------------------------------------------

def prompt(msg: str) -> str:
    return input(msg).strip()

def print_record(record: PCRecord) -> None:
    print("\n== PC ==")
    print(f"Service Tag:           {record.service_tag}")
    print(f"Modelo:                {record.modelo}")
    print(f"Fin garantía DELL:     {record.garantia_dell_fin}")
    print(f"Estado:                {record.estado.value}")
    print(f"Locación:              {record.locacion}")
    print(f"Rol:                   {record.rol}")
    print(f"Creado:                {record.created_at}")
    print(f"Actualizado:           {record.updated_at}")
    print("Historial de mantenimiento:")
    if not record.historial_mantenimiento:
        print("  (vacío)")
    else:
        for i, m in enumerate(record.historial_mantenimiento, start=1):
            print(f"  {i}. {m.fecha} · {m.tecnico} · {m.descripcion}")
    print()

def action_create(store: FileStore) -> None:
    try:
        print("\n[CREAR PC]")
        tag = normalize_service_tag(prompt("Service Tag: "))
        if store.exists(tag):
            print("Ya existe un registro con ese Service Tag.")
            return
        modelo = prompt("Modelo del equipo: ")
        garantia_fin = prompt("Fin de garantía DELL (YYYY-MM-DD): ")
        iso_date_parse(garantia_fin)
        print("Estados válidos:")
        print("  - desplegado\n  - en_stock\n  - pendiente_disposal\n  - disposed")
        estado = prompt("Estado: ")
        locacion = prompt("Locación/Área: ")
        rol = prompt("Rol (usuario, estación de producción, etc.): ")
        record = PCRecord(
            service_tag=tag,
            modelo=modelo,
            garantia_dell_fin=garantia_fin,
            estado=estado,
            locacion=locacion,
            rol=rol,
        )
        store.save(record)
        print("Registro creado.")
    except Exception as e:
        print(f"Error al crear: {e}")
        
def action_read(store: FileStore) -> None:
    try:
        tag = prompt("Service Tag a consultar: ")
        record = store.load(tag)
        print_record(record)
    except Exception as e:
        print(f"Error al leer: {e}")

def action_update(store: FileStore) -> None:
    try:
        tag = prompt("Service Tag a actualizar: ")
        record = store.load(tag)
        print("Deja en blanco para mantener el valor actual.")
        modelo = prompt(f"Modelo [{record.modelo}]: ") or record.modelo
        garantia = prompt(f"Fin garantía DELL [{record.garantia_dell_fin}]: ") or record.garantia_dell_fin
        # valida si se cambió
        if garantia != record.garantia_dell_fin:
            iso_date_parse(garantia)
        estado = prompt(f"Estado [{record.estado.value}]: ") or record.estado.value
        locacion = prompt(f"Locación [{record.locacion}]: ") or record.locacion
        rol = prompt(f"Rol [{record.rol}]: ") or record.rol
        updated = PCRecord(
            service_tag=record.service_tag,
            modelo=modelo,
            garantia_dell_fin=garantia,
            estado=estado,
            locacion=locacion,
            rol=rol,
            historial_mantenimiento=record.historial_mantenimiento,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        store.save(updated)
        print("Registro actualizado.")
    except Exception as e:
        print(f"Error al actualizar: {e}")

def action_delete(store: FileStore) -> None:
    try:
        tag = prompt("Service Tag a eliminar: ")
        confirm = prompt(f"¿Seguro que deseas eliminar '{tag}'? (si/no): ")
        if confirm.lower() in {"si", "sí", "s", "yes", "y"}:
            store.delete(tag)
            print("Registro eliminado.")
        else:
            print("(Cancelado)")
    except Exception as e:
        print(f"Error al eliminar: {e}")
    
def action_list(store: FileStore) -> None:
    records = store.list_all()
    if not records:
        print("No hay registros aún.")
        return
    print(f"\nSe encontraron {len(records)} registro(s):")
    for r in records:
        print(f"- {r.service_tag}: {r.modelo} · {r.estado.value} · Garantía fin {r.garantia_dell_fin}")

def action_add_maintenance(store: FileStore) -> None:
    try:
        tag = prompt("Service Tag: ")
        record = store.load(tag)
        print("\n[Nueva entrada de mantenimiento]")
        fecha = prompt("Fecha (YYYY-MM-DD): ")
        iso_date_parse(fecha)
        tecnico = prompt("Técnico: ")
        descripcion = prompt("Descripción: ")
        entry = MaintenanceEntry(descripcion=descripcion, fecha=fecha, tecnico=tecnico)
        record.historial_mantenimiento.append(entry)
        store.save(record)
        print("Mantenimiento agregado.")
    except Exception as e:
        print(f"Error al agregar mantenimiento: {e}")

MENU = {
    "1": ("Crear PC", action_create),
    "2": ("Leer PC (por Service Tag)", action_read),
    "3": ("Actualizar PC", action_update),
    "4": ("Eliminar PC", action_delete),
    "5": ("Listar PCs", action_list),
    "6": ("Agregar entrada de mantenimiento", action_add_maintenance),
    "0": ("Salir", None),
}

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
