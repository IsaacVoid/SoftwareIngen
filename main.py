import json
import os 


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
