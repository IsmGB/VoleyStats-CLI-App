# VoleyStats CLI App

VoleyStats is a command-line application that reads and interprets scouting data and returns the results in an Excel report. A single command is available:

```
voleystats scoutfile.txt excelfile.xlsx
```

where `scoutfile.txt` refers to the file containing the scouting data, and `excelfile.xlsx` is the file in which the report is generated. Additionally, the command accepts four optional arguments:

* `--home homefile.json`: *.json* file containing the jersey numbers, first names, and last names of the home team players.
* `--away awayfile.json`: Same as above, but for the away team players.
* `--raw rawfile.txt`: File containing the scouting data transformed into complete code sequences. The Excel report is generated from this data.
* `--config configfile.json`: Configuration file. Currently, it groups the default save paths for Excel reports, *rawfiles.txt* files, and the *.json* team files.

## Report

The report presents the information extracted from the scouting data across different sheets:

* **Summary**: Presents the data collected for each team, broken down by sets. Additionally, it presents the attack-out percentage after reception for each player and compares successful/point actions against errors for each team.
* **Data**: For each team, presents the data collected for each player, broken down by sets. As in the *Summary* sheet, successful/point actions are compared against errors for each team member.
* **ATTACK**: Provides detailed information about each player's attack actions. It presents the percentage of attack types used by each player and the attack direction of each player according to each zone at the net.
* **SERVE**: Provides detailed information about each player's serving actions. It presents the overall serve rating for each player and the rating by serve type.
* **RECEIVE**: Provides detailed information about reception for each player. It shows the overall reception rating, the rating according to the opposing server, and the rating according to the area of the court where the reception takes place.
* **OBJETIVES** (under development): Provides a sheet for determining whether the objectives of the match have been met. Objectives can be manually listed and marked in an adjacent column if they have been achieved.

The data presented in ATTACK, SERVE, and RECEIVE may be incorrect or incomplete if only basic scouting is performed (without considering extended types or court zones).

## Scouting

Each scouting command corresponds to a line in the `.txt` file. As an example, a match scouting file is provided at `tmp/scout_example.txt`. Commands are case-sensitive and the following commands are available:

* **Define match set:** **`set <id>`**. *id* can be either a numeric value or a text string.
* **Set the setter's position:** **`z<n1> az<n2>`**. *n1* and *n2* refer to the setter's rotation position on the court (1, 2, 3, 4, 5, or 6). A command preceded by `a` refers to the away team, while `*` (or no prefix) designates the home team. Both actions can be set on the same line or on separate lines.
* **Rally sequences**: Each rally is a sequence of actions performed by the home and away teams until the point ends. Each action sequence consists of up to 6 codes: team, jersey number, skill, type, extended type, zone, and rating. Certain codes can be omitted for each action, in which case the program assigns a default value:
	* Team: `*` home team (default), `a` away team.
	* Jersey number: From `1` to `99`. Cannot be omitted.
	* Skill: `A` attack, `B` block, `D` defense/support, `E` setting, `F` *free ball*, `R` reception, `S` serve.
	* Types (omitting them is recommended when using extended types): `H` high attack/standing serve (default), `M` medium attack, `N` back-row attack (basic scouting), `O` tip/other, `Q` middle attack call/power serve, `T` fast attack/float-tense serve, `U` super attack.
	* Extended types (automatically assigns type `H` or `Q`): `K` middle attack calls, `X` attack calls. Combined with numbers from `1` to `9` (e.g. `K1`, `X4`, etc.). None by default.
	* Zone: `Z` combined with numbers from `1` to `9` to designate court zones. None by default.
	* Rating: `#` double positive, `+` positive, `/` *slash*, `-` negative, `=` error, `!` exclamation. The rating system follows the instructions defined in the DataVolley4 manual. `+` positive by default.
* **Point annotation:** **`ap`**. All rally sequences must end by awarding a point to the team that won the rally: `*p` or `p` if the home team scores, and `ap` if the away team scores.
* **Player substitution:** **`c12.21 3.9`**. Each code corresponds to the jersey number of the player leaving the court and the player entering, separated by a dot. Any number of substitutions can be entered in the same sequence as long as they are separated by spaces. The first player replacement must be preceded by `c` or `*c` for the home team and `ac` for the away team. In the example, players 12 and 3 from the home team leave the court and are replaced by players 21 and 9, respectively.
* **Timeout:** **`T`**: Indicates a timeout requested by one of the two teams: `T` or `*T` for the home team, and `aT` for the away team.

## Rally Example

```
a13ST5Z5.1 2K1 7X2# p
```

Player nº 13 from the away team performs a tense/float serve from zone 5 of their court to zone 5 of the opponent's court. Player nº 1 from the home team performs a reception rated as positive `+` (rating omitted by default). Next, player nº 2 from the home team performs a `K1` attack call rated as positive. Finally, player nº 7 from the home team performs an `X2` attack call, ending the rally with a successful action. The point is awarded to the home team.

## App example

Install the application in the working directory:
```
pip install -e .
```

Execute a exmple report:
```
voleystats voleystats_example.txt excel_example.xlsx --raw raw_example.txt --home home.json
```


## Roadmap

VoleyStats CLI is currently a beta application. New features and bug fixes will be implemented in successive versions.
