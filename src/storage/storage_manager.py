import json
import os
from typing import Dict, List, Tuple
from pathlib import Path

from config.bot_config import BotConfig

class StorageManager:
    def __init__(self):
        self.storage_path = BotConfig.STORAGE_FILE_PATH
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self):
        """Create storage file if it doesn't exist"""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, 'w') as f:
                json.dump({}, f)
    
    def _load_data(self) -> Dict[str, int]:
        """Load data from storage file"""
        with open(self.storage_path, 'r') as f:
            return json.load(f)
    
    def _save_data(self, data: Dict[str, int]):
        """Save data to storage file"""
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_plate(self, plate: str):
        """Add or increment a license plate count"""
        data = self._load_data()
        data[plate] = data.get(plate, 0) + 1
        self._save_data(data)
    
    def add_plates(self, plates: List[str]):
        """Add multiple license plates"""
        data = self._load_data()
        for plate in plates:
            data[plate] = data.get(plate, 0) + 1
        self._save_data(data)
    
    def get_plate_count(self, plate: str) -> int:
        """Get count for a specific license plate"""
        data = self._load_data()
        return data.get(plate, 0)
    
    def get_all_plates(self) -> Dict[str, int]:
        """Get all license plates and their counts"""
        return self._load_data()
    
    def reset_all(self):
        """Reset all license plate counts"""
        self._save_data({})
    
    def search_plate(self, plate: str) -> Tuple[bool, int]:
        """Search for a license plate and return if found and its count"""
        count = self.get_plate_count(plate)
        return (count > 0, count)