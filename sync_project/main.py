# main.py  
import os  
from datetime import datetime  
from sync_app.services.sync_service import process_client  
   

def main():  
 base_dir = os.path.dirname(os.path.abspath(__file__))  
 #clients_path = os.path.join(base_dir, CLIENTS_ROOT_FOLDER) # REMOVE THIS  
   

 #process_client(client_folder_path, client_name)  
 print(f"\n{'='*70}\nProcesso de sincronização concluído para todos os clientes.\n{'='*70}")  
if __name__ == '__main__':  
 main()  