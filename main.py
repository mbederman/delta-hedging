from hedge_manager import Hedge_Manager
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    
    manager = Hedge_Manager()
    manager.run()