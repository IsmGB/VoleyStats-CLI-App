import json
import re
from pathlib import Path

from typing import Optional, Any, Literal



class Config:
    DEAFULT_FILE = Path(__file__).resolve().parents[2] / "config.json"

    def __init__(self, filename: str, excelfile: str, configfile: Optional[str]) -> None:
        def set_filename(filename: Path) -> Path:
            if not filename.is_absolute():
                filename = Path.cwd() / filename
            if filename.exists():
                return filename
            raise FileNotFoundError(f"{filename} does not exists.")

        def set_excelfile(excelfile: Path) -> Path:
            if not excelfile.is_absolute():
                excelfile = Config.PATHS['reports'] / excelfile
            if excelfile.suffix != '.xlsx':
                excelfile = excelfile.with_suffix(".xlsx")
            return self._check_overwrite(excelfile) if excelfile.exists() else excelfile
    
        file_path = Config.DEAFULT_FILE if configfile is None else Path(configfile)
        self.file_path = file_path if file_path.is_absolute() else Config.DEAFULT_FILE / file_path

        self.input = set_filename(Path(filename))

        config = self._load_config()
        Config.PATHS = self._get_dir_paths(config)

        self.excelfile = set_excelfile(Path(excelfile))

        self.team: dict[str, Optional[dict]] = {'home': None, 'away': None}
        self.team_path: dict[str, Optional[Path]] = {'home': None, 'away': None}
        
        self.raw: Optional[Path] = None
    

    def _load_config(self) -> Any:
        if not self.file_path.exists():
            raise ValueError(f"Configuration file '{self.file_path}' does not exist.")
        with self.file_path.open(encoding='utf-8') as f:
            return json.load(f)
    

    def _get_dir_paths(self, config: Any) -> dict[str, Path]:    
        if (paths := config.get('paths')) is None:
            raise ValueError("Key 'paths' was not found in configuration file.")
        
        dir_paths = {k: Path(v).resolve() for k,v in paths.items()}
        for k in ('reports', 'raw', 'teams'):
            if (path := dir_paths.get(k)) is None:
                raise ValueError(f"Key '{k}' was not found in configurations file.")
            if not path.exists():
                raise ValueError(f"Directory '{path}' does not exist.")    
        return dir_paths
    

    def load_team(self, team: Literal['home', 'away'], teamfile: Path) -> None:
        if not teamfile.is_absolute():
            teamfile = Config.PATHS['teams'] / teamfile
        if not teamfile.exists():
            print(f"File '{teamfile}' does not exists. Skip team '{team}'.")
            return
        
        with teamfile.open(encoding='utf-8') as f:
            try:
                team_dict = {int(k): v for k,v in json.load(f).items()}
            except ValueError as e:
                print(f"'{teamfile}': {e}. Skip team '{team}'.")
                return
            
        for n, player in team_dict.items():
            if player.get('name') is None or player.get('surname') is None:
                print(f"Cannot assign name or surname to player '{n}' in team '{team}'. Skip team '{team}'.")
                return
        
        self.team[team] = team_dict
    

    def set_raw(self, filename: Path) -> None:
        if not filename.is_absolute():
            filename = Config.PATHS['raw'] / filename
        if filename.suffix != '.txt':
            filename = filename.with_suffix(".txt")
        self.raw = self._check_overwrite(filename) if filename.exists() else filename
    

    def _check_overwrite(self, filename: Path) -> Path:
        ans = input(f"'{filename}' already exists. Overwrite? [y/n]: ")
        if ans == 'y':
            return filename
        if ans == 'n':
            stem = filename.stem
            if (match := re.search(r"\(\d+\)$", stem)):
                i = int(match.group(1))
                base = stem[:match.start()].rstrip()
            else:
                i = 1
                base = stem
            
            while filename.exists():
                filename = filename.with_stem(f"{base} ({i})")
                i += 1
            return filename
        raise ValueError(f"'{ans}' is not a valid choice. Exit program.")

        

            
                

        
        



