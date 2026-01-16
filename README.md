# NBA Player FG% Stats

An interactive web application for viewing and analyzing NBA player field goal percentage (FG%) statistics with support for traded players and combined team stats.

## Features

- **Live Data Scraping**: Automatically scrapes current NBA player stats from basketball-reference.com
- **Traded Player Handling**: Intelligently handles players traded mid-season by using combined 2TM (2-Team) stats
- **Interactive Filtering**: Filter players by team and search by player name
- **Sortable Columns**: Click column headers to sort by any statistic
- **Responsive Design**: Clean, modern HTML interface with color-coded stats
- **Statistics Tracked**:
  - FG% (Field Goal Percentage)
  - 2P% (2-Point Percentage)
  - 3P% (3-Point Percentage)
  - Made 2 Likelihood (based on shot distribution)
  - First Made Prediction (Weighted)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/nbafirstfg.git
cd nbafirstfg
```

2. Create a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On macOS/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the script:
```bash
python nbafg.py
```

This will:
1. Scrape the latest NBA player stats from basketball-reference.com
2. Process traded players to use their combined 2TM stats
3. Generate an interactive HTML file (`index.html`)
4. Open the stats in your browser

## Configuration

### Adding Traded Players

Edit the `apply_manual_team_adjustments()` function to add or modify traded players:

```python
adjustments = {
    'Player Name': 'FINAL_TEAM',  # Example comment
}
```

The system will:
1. Find the 2TM row (combined stats) for the player
2. Reassign their team to the specified final team
3. Keep all their combined statistics

## Requirements

- Python 3.7+
- Selenium
- BeautifulSoup4
- Chrome/Chromium browser
- WebDriver Manager

## Data Source

Stats are scraped from [Basketball Reference](https://www.basketball-reference.com/leagues/NBA_2026_totals.html)

## License

MIT License - feel free to use this project however you'd like!

## Notes

- The script uses headless Chrome for web scraping
- If scraping fails, it falls back to sample data
- Players with fewer than 15 games are averaged with previous season stats for reliability
