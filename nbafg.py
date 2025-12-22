import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import datetime

def scrape_dunk_stats():
    """
    Scrape NBA player dunk stats from basketball-reference.com shooting page
    Returns a list with player dunk stats including Dunks % FGA and Dunks count
    """
    print("Scraping NBA player dunk stats from basketball-reference.com...")
    
    driver = None
    try:
        # Set up Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        url = "https://www.basketball-reference.com/leagues/NBA_2026_shooting.html"
        print(f"Loading {url}...")
        driver.get(url)
        
        # Wait for table to load
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "tbody"))
            )
        except:
            print("Timeout waiting for table")
            driver.quit()
            return None
        
        time.sleep(2)
        
        # Parse the page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table')
        
        if not table:
            print("Could not find table")
            driver.quit()
            return None
        
        # Build header -> index map from table header
        header_to_idx = {}
        thead = table.find('thead')
        if thead:
            header_rows = thead.find_all('tr')
            header_cells = header_rows[-1].find_all('th')
        else:
            header_cells = []
        
        for idx, th in enumerate(header_cells):
            data_stat = th.get('data-stat')
            text = th.get_text(strip=True)
            if data_stat:
                header_to_idx[data_stat] = idx
            if text:
                header_to_idx[text] = idx
        
        # Find column indices for dunk stats
        # Looking for: Dunks (dunk_pct), Dunks count (dunk)
        candidates = {
            'dunk_pct': ['dunk_pct', 'Dunk%', 'Dunks %FGA'],
            'dunk': ['dunk', 'Dunks', 'Dunks #'],
        }
        
        idx_map = {}
        for key, names in candidates.items():
            for name in names:
                if name in header_to_idx:
                    idx_map[key] = header_to_idx[name]
                    break
        
        rows = table.find_all('tr')[1:]  # Get all data rows
        players = []
        
        print(f"Found {len(rows)} rows")
        print(f"Detected header indices: {idx_map}")
        
        for row in rows:
            cells = row.find_all(['th', 'td'])
            if not cells:
                continue
            
            try:
                # Extract player name from link with href containing /players/
                player_name = None
                for cell in cells[:4]:
                    link = cell.find('a')
                    if link and '/players/' in str(link.get('href', '')):
                        player_name = link.text.strip()
                        break
                
                # Skip rows without player link
                if not player_name or player_name.isdigit():
                    continue
                
                col_values = [cell.text.strip() for cell in cells]
                
                # Find team - NBA team abbreviations
                nba_teams = ['ATL', 'BOS', 'BRK', 'CHO', 'CHI', 'CLE', 'DAL', 'DEN', 'DET', 'GSW', 'HOU', 'IND', 'LAC', 'LAL', 
                             'MEM', 'MIA', 'MIL', 'MIN', 'NOP', 'NYK', 'OKC', 'ORL', 'PHI', 'PHO', 'POR', 'SAC', 'SAS', 
                             'TOR', 'UTA', 'WAS']
                
                team = None
                for val in col_values:
                    if val in nba_teams:
                        team = val
                        break
                
                if team == 'PHO':
                    team = 'PHX'
                
                if not team:
                    continue
                
                # Helper to safely parse floats at specific indices
                def parse_at(key):
                    try:
                        idx = idx_map.get(key)
                        if idx is None or idx >= len(cells):
                            return 0.0
                        val_str = cells[idx].text.strip()
                        return float(val_str) if val_str else 0.0
                    except:
                        return 0.0
                
                # Helper to safely parse integers
                def parse_int_at(key):
                    try:
                        idx = idx_map.get(key)
                        if idx is None or idx >= len(cells):
                            return 0
                        val_str = cells[idx].text.strip()
                        return int(val_str) if val_str else 0
                    except:
                        return 0
                
                dunk_pct = parse_at('dunk_pct')
                dunk_count = parse_int_at('dunk')
                
                players.append({
                    'Player': player_name,
                    'Team': team,
                    'Dunk %FGA': round(dunk_pct, 3),
                    'Dunks': dunk_count,
                })
            except Exception as e:
                continue
        
        driver.quit()
        
        if len(players) > 100:
            print(f"✅ Successfully scraped {len(players)} live NBA players dunk stats!")
            return players
        else:
            print(f"Only found {len(players)} players")
            return None
            
    except Exception as e:
        if driver:
            try:
                driver.quit()
            except:
                pass
        print(f"Scraping failed: {str(e)[:150]}")
        return None


def scrape_nba_stats():
    """
    Scrape NBA player FG% data from basketball-reference.com using Selenium
    Returns a list with player stats including FG%, 2P%, 3P%
    """
    print("Scraping NBA player stats from basketball-reference.com...")
    
    driver = None
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        import time
        
        # Set up Chrome options
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        url = "https://www.basketball-reference.com/leagues/NBA_2026_totals.html"
        print(f"Loading {url}...")
        driver.get(url)
        
        # Wait for table to load
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_all_elements_located((By.TAG_NAME, "tbody"))
            )
        except:
            print("Timeout waiting for table")
            driver.quit()
            return None
        
        time.sleep(2)
        
        # Parse the page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        table = soup.find('table')
        
        if not table:
            print("Could not find table")
            driver.quit()
            return None
        
        # We'll fetch last year's totals as a fallback for low-appearance players
        prev_url = "https://www.basketball-reference.com/leagues/NBA_2025_totals.html"

        # Save current page soup/table
        soup_curr = soup
        table_curr = table

        # Load previous year page
        try:
            driver.get(prev_url)
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'tbody')))
            time.sleep(1)
            soup_prev = BeautifulSoup(driver.page_source, 'html.parser')
            table_prev = soup_prev.find('table')
        except Exception:
            table_prev = None

        def build_idx_map(table_obj):
            hdr_map = {}
            if not table_obj:
                return hdr_map
            thead = table_obj.find('thead')
            if thead:
                header_rows = thead.find_all('tr')
                header_cells = header_rows[-1].find_all('th')
            else:
                header_cells = []
            for idx, th in enumerate(header_cells):
                data_stat = th.get('data-stat')
                text = th.get_text(strip=True)
                if data_stat:
                    hdr_map[data_stat] = idx
                if text:
                    hdr_map[text] = idx
            return hdr_map

        # Candidates for columns
        candidates = {
            'rank': ['rank', 'Rk', '#'],
            'g': ['g', 'G', 'games'],
            'fg_pct': ['fg_pct', 'FG%'],
            'fg2': ['fg2', '2P'],
            'fg2a': ['fg2a', '2PA'],
            'fg3': ['fg3', '3P'],
            'fg3a': ['fg3a', '3PA'],
        }

        hdr_curr = build_idx_map(table_curr)
        hdr_prev = build_idx_map(table_prev)

        def find_idx(hdr_map, candidates_list):
            for c in candidates_list:
                if c in hdr_map:
                    return hdr_map[c]
            return None

        idx_map_curr = {}
        idx_map_prev = {}
        for key, names in candidates.items():
            idx_map_curr[key] = find_idx(hdr_curr, names)
            idx_map_prev[key] = find_idx(hdr_prev, names)

        # Build previous-year lookup mapping player_name -> stats (if table_prev present)
        prev_stats = {}
        if table_prev:
            for r in table_prev.find_all('tr')[1:]:
                cells_prev = r.find_all(['th', 'td'])
                if not cells_prev:
                    continue
                # extract player name via link
                pname = None
                for c in cells_prev[:4]:
                    a = c.find('a')
                    if a and '/players/' in str(a.get('href', '')):
                        pname = a.text.strip()
                        break
                if not pname:
                    continue

                def parse_val(cells, idx, is_int=False):
                    try:
                        if idx is None or idx >= len(cells):
                            return 0 if is_int else 0.0
                        txt = cells[idx].get_text(strip=True)
                        if txt == '':
                            return 0 if is_int else 0.0
                        return int(txt) if is_int else float(txt)
                    except:
                        return 0 if is_int else 0.0

                prev_fg_pct = parse_val(cells_prev, idx_map_prev.get('fg_pct'))
                prev_rank = parse_val(cells_prev, idx_map_prev.get('rank'), is_int=True)
                prev_fg2 = parse_val(cells_prev, idx_map_prev.get('fg2'), is_int=True)
                prev_fg2a = parse_val(cells_prev, idx_map_prev.get('fg2a'), is_int=True)
                prev_fg3 = parse_val(cells_prev, idx_map_prev.get('fg3'), is_int=True)
                prev_fg3a = parse_val(cells_prev, idx_map_prev.get('fg3a'), is_int=True)
                prev_g = parse_val(cells_prev, idx_map_prev.get('g'), is_int=True)

                prev_stats[pname] = {
                    'rank': prev_rank,
                    'fg_pct': prev_fg_pct,
                    'fg2': prev_fg2,
                    'fg2a': prev_fg2a,
                    'fg3': prev_fg3,
                    'fg3a': prev_fg3a,
                    'g': prev_g,
                }

        # Now prepare to process current-year rows
        rows = table_curr.find_all('tr')[1:]
        players = []
        
        print(f"Found {len(rows)} rows")
        print(f"Detected header indices (current): {idx_map_curr}")

        for row in rows:
            cells = row.find_all(['th', 'td'])
            if not cells:
                continue
            
            try:
                # Extract player name from link with href containing /players/
                player_name = None
                for cell in cells[:4]:
                    link = cell.find('a')
                    if link and '/players/' in str(link.get('href', '')):
                        player_name = link.text.strip()
                        break
                
                # Skip rows without player link
                if not player_name or player_name.isdigit():
                    continue
                
                col_values = [cell.text.strip() for cell in cells]
                
                # Find team - NBA team abbreviations
                nba_teams = ['ATL', 'BOS', 'BRK', 'CHO', 'CHI', 'CLE', 'DAL', 'DEN', 'DET', 'GSW', 'HOU', 'IND', 'LAC', 'LAL', 
                             'MEM', 'MIA', 'MIL', 'MIN', 'NOP', 'NYK', 'OKC', 'ORL', 'PHI', 'PHO', 'POR', 'SAC', 'SAS', 
                             'TOR', 'UTA', 'WAS']
                
                team = None
                for val in col_values:
                    if val in nba_teams:
                        team = val
                        break
                
                if team == 'PHO':
                    team = 'PHX'
                
                if not team:
                    continue
                
                # Helper to safely parse floats at specific indices
                def parse_at(key):
                    try:
                        idx = idx_map_curr.get(key)
                        if idx is None or idx >= len(cells):
                            return 0.0
                        val_str = cells[idx].text.strip()
                        return float(val_str) if val_str else 0.0
                    except:
                        return 0.0
                
                # Helper to safely parse integers (for rank)
                def parse_int_at(key):
                    try:
                        idx = idx_map_curr.get(key)
                        if idx is None or idx >= len(cells):
                            return None
                        val_str = cells[idx].text.strip()
                        return int(val_str) if val_str else None
                    except:
                        return None
                
                rank = parse_int_at('rank')
                fg_pct = parse_at('fg_pct')
                fg2_made = parse_at('fg2')
                fg2_att = parse_at('fg2a')
                fg3_made = parse_at('fg3')
                fg3_att = parse_at('fg3a')
                current_g = parse_int_at('g') or 0

                # Helper to canonicalize names (remove Jr./Sr. suffixes and dots)
                def canon_name(n):
                    if not n:
                        return n
                    s = n.replace('.', '').replace(',', '')
                    tokens = s.split()
                    # remove common suffixes
                    suffixes = set(['Jr', 'Sr', 'II', 'III', 'IV'])
                    if tokens and tokens[-1] in suffixes:
                        tokens = tokens[:-1]
                    return ' '.join(tokens)

                used_prev = False
                # If player has less than 15 games, try to average with previous season totals
                if current_g < 15 and prev_stats:
                    prev = prev_stats.get(player_name)
                    if not prev:
                        prev = prev_stats.get(canon_name(player_name))
                    if prev and prev.get('g', 0) > 0:
                        try:
                            # convert current to ints where appropriate
                            c_fg2 = int(round(fg2_made))
                            c_fg2a = int(round(fg2_att))
                            c_fg3 = int(round(fg3_made))
                            c_fg3a = int(round(fg3_att))

                            p_fg2 = int(prev.get('fg2', 0))
                            p_fg2a = int(prev.get('fg2a', 0))
                            p_fg3 = int(prev.get('fg3', 0))
                            p_fg3a = int(prev.get('fg3a', 0))

                            # Average the raw totals
                            avg_fg2 = (c_fg2 + p_fg2) / 2.0
                            avg_fg2a = (c_fg2a + p_fg2a) / 2.0
                            avg_fg3 = (c_fg3 + p_fg3) / 2.0
                            avg_fg3a = (c_fg3a + p_fg3a) / 2.0

                            # Recompute percentages from averaged totals
                            two_pct = (avg_fg2 / avg_fg2a) if avg_fg2a > 0 else 0.0
                            three_pct = (avg_fg3 / avg_fg3a) if avg_fg3a > 0 else 0.0
                            total_made = avg_fg2 + avg_fg3
                            total_att = avg_fg2a + avg_fg3a
                            fg_pct = (total_made / total_att) if total_att > 0 else fg_pct

                            # Recompute likelihoods based on averaged made counts
                            if total_made > 0:
                                made2_likelihood = (avg_fg2 / total_made) * 100.0
                            else:
                                made2_likelihood = 0.0

                            if avg_fg2 > avg_fg3:
                                first_made_weighted = 'Made 2 (Avg)'
                            elif avg_fg3 > avg_fg2:
                                first_made_weighted = 'Made 3 (Avg)'
                            else:
                                first_made_weighted = 'Tied (Avg)'

                            # Choose the better (higher) ranking between current and previous year
                            try:
                                prev_rank_val = prev.get('rank') if isinstance(prev.get('rank'), int) else None
                                cur_rank_val = rank if isinstance(rank, int) else None
                                if cur_rank_val is None and prev_rank_val is not None:
                                    rank = prev_rank_val
                                elif prev_rank_val is None and cur_rank_val is not None:
                                    rank = cur_rank_val
                                elif prev_rank_val is not None and cur_rank_val is not None:
                                    # lower numeric rank is better (1 is best) -> choose min
                                    rank = min(cur_rank_val, prev_rank_val)
                            except Exception:
                                pass

                            used_prev = True
                        except Exception:
                            # fallback to current-year calculations if averaging fails
                            used_prev = False

                if not used_prev:
                    # Calculate 2P% and 3P% from made/attempts
                    two_pct = (fg2_made / fg2_att) if fg2_att > 0 else 0.0
                    three_pct = (fg3_made / fg3_att) if fg3_att > 0 else 0.0
                    # Calculate weighted first-made based on made counts
                    made_total = fg2_made + fg3_made
                    if made_total > 0:
                        made2_likelihood = (fg2_made / made_total) * 100.0
                    else:
                        made2_likelihood = 0.0

                    if fg2_made > fg3_made:
                        first_made_weighted = 'Made 2'
                    elif fg3_made > fg2_made:
                        first_made_weighted = 'Made 3'
                    else:
                        first_made_weighted = 'Tied'
                
                # end processing for this player
                
                players.append({
                    'Player': player_name,
                    'Team': team,
                    'Rank': rank,
                    'FG%': round(fg_pct, 3),
                    '2P%': round(two_pct, 3),
                    '3P%': round(three_pct, 3),
                    'First Made (Weighted)': first_made_weighted,
                    'Made 2 Likelihood (counts)': round(made2_likelihood, 1),
                })
            except Exception as e:
                continue
        
        driver.quit()
        
        if len(players) > 100:
            print(f"✅ Successfully scraped {len(players)} live NBA players!")
            return players
        else:
            print(f"Only found {len(players)} players")
            return None
            
    except Exception as e:
        if driver:
            try:
                driver.quit()
            except:
                pass
        print(f"Scraping failed: {str(e)[:150]}")
        return None


def create_sample_data():
    """
    Create comprehensive sample data with all 30 NBA teams and realistic rosters
    """
    data = [
        # Atlanta Hawks
        {'Player': 'Trae Young', 'Team': 'ATL', 'FG%': 0.435, '2P%': 0.420, '3P%': 0.350},
        {'Player': 'Clint Capela', 'Team': 'ATL', 'FG%': 0.665, '2P%': 0.675, '3P%': 0.000},
        {'Player': 'Bogdan Bogdanovic', 'Team': 'ATL', 'FG%': 0.465, '2P%': 0.410, '3P%': 0.395},
        {'Player': 'De\'Andre Hunter', 'Team': 'ATL', 'FG%': 0.430, '2P%': 0.445, '3P%': 0.360},
        
        # Boston Celtics
        {'Player': 'Jayson Tatum', 'Team': 'BOS', 'FG%': 0.485, '2P%': 0.540, '3P%': 0.375},
        {'Player': 'Jrue Holiday', 'Team': 'BOS', 'FG%': 0.440, '2P%': 0.480, '3P%': 0.340},
        {'Player': 'Derrick White', 'Team': 'BOS', 'FG%': 0.460, '2P%': 0.510, '3P%': 0.380},
        {'Player': 'Kristaps Porzingis', 'Team': 'BOS', 'FG%': 0.510, '2P%': 0.555, '3P%': 0.420},
        {'Player': 'Al Horford', 'Team': 'BOS', 'FG%': 0.510, '2P%': 0.545, '3P%': 0.360},
        
        # Brooklyn Nets
        {'Player': 'Cameron Thomas', 'Team': 'BRK', 'FG%': 0.445, '2P%': 0.460, '3P%': 0.360},
        {'Player': 'Mikal Bridges', 'Team': 'BRK', 'FG%': 0.475, '2P%': 0.500, '3P%': 0.395},
        {'Player': 'Dennis Schroder', 'Team': 'BRK', 'FG%': 0.455, '2P%': 0.490, '3P%': 0.360},
        
        # Charlotte Hornets
        {'Player': 'LaMelo Ball', 'Team': 'CHA', 'FG%': 0.415, '2P%': 0.430, '3P%': 0.330},
        {'Player': 'Brandon Miller', 'Team': 'CHA', 'FG%': 0.440, '2P%': 0.450, '3P%': 0.370},
        
        # Chicago Bulls
        {'Player': 'DeMar DeRozan', 'Team': 'CHI', 'FG%': 0.500, '2P%': 0.545, '3P%': 0.280},
        {'Player': 'Zach LaVine', 'Team': 'CHI', 'FG%': 0.450, '2P%': 0.470, '3P%': 0.375},
        {'Player': 'Nikola Vucevic', 'Team': 'CHI', 'FG%': 0.530, '2P%': 0.580, '3P%': 0.300},
        
        # Cleveland Cavaliers
        {'Player': 'Donovan Mitchell', 'Team': 'CLE', 'FG%': 0.460, '2P%': 0.480, '3P%': 0.380},
        {'Player': 'Darius Garland', 'Team': 'CLE', 'FG%': 0.440, '2P%': 0.460, '3P%': 0.340},
        {'Player': 'Evan Mobley', 'Team': 'CLE', 'FG%': 0.540, '2P%': 0.585, '3P%': 0.250},
        
        # Dallas Mavericks
        {'Player': 'Luka Doncic', 'Team': 'DAL', 'FG%': 0.470, '2P%': 0.505, '3P%': 0.385},
        {'Player': 'Kyrie Irving', 'Team': 'DAL', 'FG%': 0.445, '2P%': 0.450, '3P%': 0.440},
        {'Player': 'Tim Hardaway Jr.', 'Team': 'DAL', 'FG%': 0.380, '2P%': 0.390, '3P%': 0.360},
        {'Player': 'P.J. Washington', 'Team': 'DAL', 'FG%': 0.420, '2P%': 0.460, '3P%': 0.380},
        
        # Denver Nuggets
        {'Player': 'Nikola Jokic', 'Team': 'DEN', 'FG%': 0.565, '2P%': 0.600, '3P%': 0.410},
        {'Player': 'Jamal Murray', 'Team': 'DEN', 'FG%': 0.440, '2P%': 0.470, '3P%': 0.380},
        {'Player': 'Christian Braun', 'Team': 'DEN', 'FG%': 0.420, '2P%': 0.460, '3P%': 0.370},
        {'Player': 'Aaron Gordon', 'Team': 'DEN', 'FG%': 0.490, '2P%': 0.530, '3P%': 0.360},
        
        # Detroit Pistons
        {'Player': 'Cade Cunningham', 'Team': 'DET', 'FG%': 0.450, '2P%': 0.480, '3P%': 0.350},
        {'Player': 'Isaiah Stewart', 'Team': 'DET', 'FG%': 0.550, '2P%': 0.575, '3P%': 0.200},
        
        # Golden State Warriors
        {'Player': 'Stephen Curry', 'Team': 'GSW', 'FG%': 0.465, '2P%': 0.420, '3P%': 0.430},
        {'Player': 'Klay Thompson', 'Team': 'GSW', 'FG%': 0.425, '2P%': 0.350, '3P%': 0.410},
        {'Player': 'Andrew Wiggins', 'Team': 'GSW', 'FG%': 0.485, '2P%': 0.530, '3P%': 0.380},
        
        # Houston Rockets
        {'Player': 'Alperen Sengun', 'Team': 'HOU', 'FG%': 0.555, '2P%': 0.595, '3P%': 0.310},
        {'Player': 'Fred VanVleet', 'Team': 'HOU', 'FG%': 0.420, '2P%': 0.380, '3P%': 0.390},
        
        # LA Clippers
        {'Player': 'Kawhi Leonard', 'Team': 'LAC', 'FG%': 0.505, '2P%': 0.545, '3P%': 0.400},
        {'Player': 'Paul George', 'Team': 'LAC', 'FG%': 0.440, '2P%': 0.460, '3P%': 0.370},
        {'Player': 'Russell Westbrook', 'Team': 'LAC', 'FG%': 0.425, '2P%': 0.480, '3P%': 0.280},
        
        # LA Lakers
        {'Player': 'LeBron James', 'Team': 'LAL', 'FG%': 0.500, '2P%': 0.540, '3P%': 0.395},
        {'Player': 'Anthony Davis', 'Team': 'LAL', 'FG%': 0.535, '2P%': 0.595, '3P%': 0.270},
        {'Player': 'Austin Reaves', 'Team': 'LAL', 'FG%': 0.475, '2P%': 0.510, '3P%': 0.390},
        {'Player': 'Rui Hachimura', 'Team': 'LAL', 'FG%': 0.495, '2P%': 0.530, '3P%': 0.350},
        
        # Memphis Grizzlies
        {'Player': 'Ja Morant', 'Team': 'MEM', 'FG%': 0.480, '2P%': 0.550, '3P%': 0.310},
        {'Player': 'Desmond Bane', 'Team': 'MEM', 'FG%': 0.465, '2P%': 0.480, '3P%': 0.410},
        
        # Miami Heat
        {'Player': 'Jimmy Butler', 'Team': 'MIA', 'FG%': 0.480, '2P%': 0.520, '3P%': 0.330},
        {'Player': 'Bam Adebayo', 'Team': 'MIA', 'FG%': 0.510, '2P%': 0.560, '3P%': 0.200},
        {'Player': 'Tyrese Maxey', 'Team': 'MIA', 'FG%': 0.460, '2P%': 0.490, '3P%': 0.400},
        
        # Milwaukee Bucks
        {'Player': 'Giannis Antetokounmpo', 'Team': 'MIL', 'FG%': 0.530, '2P%': 0.565, '3P%': 0.390},
        {'Player': 'Damian Lillard', 'Team': 'MIL', 'FG%': 0.420, '2P%': 0.380, '3P%': 0.490},
        {'Player': 'Khris Middleton', 'Team': 'MIL', 'FG%': 0.445, '2P%': 0.490, '3P%': 0.360},
        {'Player': 'Brook Lopez', 'Team': 'MIL', 'FG%': 0.480, '2P%': 0.520, '3P%': 0.350},
        
        # Minnesota Timberwolves
        {'Player': 'Anthony Edwards', 'Team': 'MIN', 'FG%': 0.445, '2P%': 0.480, '3P%': 0.370},
        {'Player': 'Karl-Anthony Towns', 'Team': 'MIN', 'FG%': 0.450, '2P%': 0.380, '3P%': 0.410},
        
        # New Orleans Pelicans
        {'Player': 'Zion Williamson', 'Team': 'NOP', 'FG%': 0.575, '2P%': 0.615, '3P%': 0.250},
        {'Player': 'Brandon Ingram', 'Team': 'NOP', 'FG%': 0.465, '2P%': 0.510, '3P%': 0.340},
        
        # New York Knicks
        {'Player': 'Julius Randle', 'Team': 'NYK', 'FG%': 0.465, '2P%': 0.505, '3P%': 0.330},
        {'Player': 'Jalen Brunson', 'Team': 'NYK', 'FG%': 0.480, '2P%': 0.510, '3P%': 0.400},
        
        # Oklahoma City Thunder
        {'Player': 'Shai Gilgeous-Alexander', 'Team': 'OKC', 'FG%': 0.520, '2P%': 0.560, '3P%': 0.410},
        {'Player': 'Jalen Williams', 'Team': 'OKC', 'FG%': 0.445, '2P%': 0.480, '3P%': 0.370},
        {'Player': 'Lu Dort', 'Team': 'OKC', 'FG%': 0.380, '2P%': 0.390, '3P%': 0.340},
        {'Player': 'Chet Holmgren', 'Team': 'OKC', 'FG%': 0.530, '2P%': 0.580, '3P%': 0.380},
        
        # Orlando Magic
        {'Player': 'Paolo Banchero', 'Team': 'ORL', 'FG%': 0.475, '2P%': 0.520, '3P%': 0.360},
        {'Player': 'Franz Wagner', 'Team': 'ORL', 'FG%': 0.480, '2P%': 0.510, '3P%': 0.380},
        
        # Philadelphia 76ers
        {'Player': 'Joel Embiid', 'Team': 'PHI', 'FG%': 0.540, '2P%': 0.580, '3P%': 0.350},
        {'Player': 'Tyrese Maxey', 'Team': 'PHI', 'FG%': 0.460, '2P%': 0.490, '3P%': 0.400},
        
        # Phoenix Suns
        {'Player': 'Kevin Durant', 'Team': 'PHX', 'FG%': 0.510, '2P%': 0.560, '3P%': 0.420},
        {'Player': 'Devin Booker', 'Team': 'PHX', 'FG%': 0.460, '2P%': 0.460, '3P%': 0.450},
        {'Player': 'Bradley Beal', 'Team': 'PHX', 'FG%': 0.440, '2P%': 0.450, '3P%': 0.410},
        {'Player': 'Jusuf Nurkic', 'Team': 'PHX', 'FG%': 0.520, '2P%': 0.575, '3P%': 0.280},
        
        # Portland Trail Blazers
        {'Player': 'Damian Lillard', 'Team': 'POR', 'FG%': 0.420, '2P%': 0.380, '3P%': 0.490},
        {'Player': 'Anfernee Simons', 'Team': 'POR', 'FG%': 0.440, '2P%': 0.450, '3P%': 0.380},
        
        # Sacramento Kings
        {'Player': 'De\'Aaron Fox', 'Team': 'SAC', 'FG%': 0.475, '2P%': 0.520, '3P%': 0.350},
        {'Player': 'Domantas Sabonis', 'Team': 'SAC', 'FG%': 0.550, '2P%': 0.600, '3P%': 0.300},
        
        # San Antonio Spurs
        {'Player': 'Victor Wembanyama', 'Team': 'SAS', 'FG%': 0.500, '2P%': 0.540, '3P%': 0.360},
        {'Player': 'Chris Paul', 'Team': 'SAS', 'FG%': 0.430, '2P%': 0.450, '3P%': 0.370},
        
        # Toronto Raptors
        {'Player': 'Scottie Barnes', 'Team': 'TOR', 'FG%': 0.485, '2P%': 0.530, '3P%': 0.310},
        {'Player': 'Pascal Siakam', 'Team': 'TOR', 'FG%': 0.525, '2P%': 0.570, '3P%': 0.300},
        
        # Utah Jazz
        {'Player': 'Donovan Mitchell', 'Team': 'UTA', 'FG%': 0.460, '2P%': 0.480, '3P%': 0.380},
        {'Player': 'Lauri Markkanen', 'Team': 'UTA', 'FG%': 0.490, '2P%': 0.500, '3P%': 0.410},
        
        # Washington Wizards
        {'Player': 'Jordan Poole', 'Team': 'WAS', 'FG%': 0.440, '2P%': 0.420, '3P%': 0.370},
        {'Player': 'Kristaps Porzingis', 'Team': 'WAS', 'FG%': 0.510, '2P%': 0.555, '3P%': 0.420},
    ]
    return data


def add_team_rankings(players_data):
    """
    Add team-based ranking to each player (1 = best FG% on team, n = worst)
    """
    # Group players by team
    teams = {}
    for player in players_data:
        team = player['Team']
        if team not in teams:
            teams[team] = []
        teams[team].append(player)
    
    # Rank within each team by FG%
    for team, team_players in teams.items():
        # Sort by FG% descending
        sorted_team = sorted(team_players, key=lambda x: x['FG%'], reverse=True)
        for rank, player in enumerate(sorted_team, 1):
            player['Team Rank'] = rank
            player['Team Total Players'] = len(sorted_team)
    
    return players_data


def add_first_made_calculation(players_data):
    """
    Add calculated 'First Made' field to player data based on 2P% vs 3P%
    Compares shooting percentages to estimate which is more likely made first
    """
    for player in players_data:
        # If already has First Made field, skip
        if 'First Made' in player:
            continue
        
        two_pct = player.get('2P%', 0)
        three_pct = player.get('3P%', 0)
        
        if two_pct > three_pct:
            player['First Made'] = 'Made 2'
        elif three_pct > two_pct:
            player['First Made'] = 'Made 3'
        else:
            player['First Made'] = 'Tied'
    
    return players_data


def create_interactive_html(players_data):
    """
    Create an interactive HTML table with team filtering
    """
    # Get today's date for last updated
    today = datetime.date.today().strftime("%B %d, %Y")
    
    # All 30 NBA teams - include all in dropdown even if some have no players
    all_nba_teams = ['ATL', 'BOS', 'BRK', 'CHO', 'CHI', 'CLE', 'DAL', 'DEN', 'DET', 'GSW', 'HOU', 'IND', 'LAC', 'LAL', 
                     'MEM', 'MIA', 'MIL', 'MIN', 'NOP', 'NYK', 'OKC', 'ORL', 'PHI', 'PHX', 'POR', 'SAC', 'SAS', 
                     'TOR', 'UTA', 'WAS']
    teams_in_data = set(p['Team'] for p in players_data)
    # Use all NBA teams for dropdown, but keep teams_in_data for reference
    teams = sorted(all_nba_teams)
    
    # Convert data to JSON
    players_json = json.dumps(players_data)
    
    html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NBA Player FG% Stats</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            padding: 30px;
        }}
        
        h1 {{
            color: #1e3c72;
            margin-bottom: 10px;
            text-align: center;
        }}
        
        .subtitle {{
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }}
        
        .controls {{
            margin-bottom: 25px;
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        label {{
            font-weight: 600;
            color: #333;
            font-size: 16px;
        }}
        
        select {{
            padding: 10px 15px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            cursor: pointer;
            background-color: white;
            min-width: 150px;
            transition: border-color 0.3s;
        }}
        
        select:hover {{
            border-color: #2a5298;
        }}
        
        select:focus {{
            outline: none;
            border-color: #1e3c72;
            box-shadow: 0 0 5px rgba(30, 60, 114, 0.3);
        }}
        
        .search-box {{
            flex: 1;
            min-width: 200px;
        }}
        
        .search-box input {{
            width: 100%;
            padding: 10px 15px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            transition: border-color 0.3s;
        }}
        
        .search-box input:focus {{
            outline: none;
            border-color: #1e3c72;
            box-shadow: 0 0 5px rgba(30, 60, 114, 0.3);
        }}
        
        button {{
            padding: 10px 20px;
            background-color: #1e3c72;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            font-weight: 600;
            transition: background-color 0.3s;
        }}
        
        button:hover {{
            background-color: #2a5298;
        }}
        
        .table-wrapper {{
            overflow-x: auto;
            border-radius: 5px;
            border: 1px solid #ddd;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 15px;
        }}
        
        thead {{
            background-color: #1e3c72;
            color: white;
            font-weight: 600;
            position: sticky;
            top: 0;
        }}
        
        th {{
            padding: 15px;
            text-align: left;
            border-bottom: 2px solid #2a5298;
            cursor: pointer;
            user-select: none;
        }}
        
        th:hover {{
            background-color: #2a5298;
        }}
        
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }}
        
        tbody tr {{
            transition: background-color 0.2s;
        }}
        
        tbody tr:hover {{
            background-color: #f8f9ff;
        }}
        
        tbody tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        
        .stat {{
            font-weight: 500;
            color: #1e3c72;
        }}
        
        .high-stat {{
            background-color: #d4edda;
            color: #155724;
        }}
        
        .medium-stat {{
            background-color: #fff3cd;
            color: #856404;
        }}
        
        .low-stat {{
            background-color: #f8d7da;
            color: #721c24;
        }}
        
        .info {{
            text-align: center;
            color: #666;
            padding: 20px;
            font-size: 14px;
        }}
        
        .stat-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 13px;
            font-weight: 600;
            background-color: #e7f3ff;
            color: #1e3c72;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏀 NBA Player Field Goal Percentage Stats</h1>
        <p class="subtitle">2024-2026 Season(s) | Interactive Filtering by Team | Last Updated: {today}</p>
        
        <div class="controls">
            <label for="teamFilter">Filter by Team:</label>
            <select id="teamFilter" onchange="filterTable()">
                <option value="">All Teams</option>
                {"".join([f'<option value="{team}">{team}</option>' for team in teams])}
            </select>
            
            <div class="search-box">
                <input type="text" id="playerSearch" placeholder="Search player name..." onkeyup="filterTable()">
            </div>
            
            <button onclick="resetFilters()">Reset Filters</button>
        </div>
        
        <div class="table-wrapper">
            <table id="statsTable">
                <thead>
                    <tr>
                        <th onclick="sortTable(0)">Rank ↕</th>
                        <th onclick="sortTable(1)">Player Name ↕</th>
                        <th onclick="sortTable(2)">Team ↕</th>
                        <th onclick="sortTable(3)">FG% ↕</th>
                        <th onclick="sortTable(4)">2P% ↕</th>
                        <th onclick="sortTable(5)">3P% ↕</th>
                        <th onclick="sortTable(6)">Made 2 Likelihood % ↕</th>
                        <th onclick="sortTable(7)">First Made (Weighted) ↕</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                </tbody>
            </table>
        </div>
        
        <div class="info" id="resultInfo"></div>
    </div>
    
    <script>
        // Data from Python
        const allPlayers = {players_json};
        let currentData = [...allPlayers];
        let sortAscending = {{}};
        
        // Populate table
        function populateTable(data) {{
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';
            
            if (data.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="8" class="info">No players found matching your filters.</td></tr>';
                document.getElementById('resultInfo').textContent = 'No results found.';
                return;
            }}
            
            data.forEach(player => {{
                const row = document.createElement('tr');
                const rank = player['Rank'] !== undefined ? player['Rank'] : 'N/A';
                const fgPercent = (player['FG%'] * 100).toFixed(1);
                const twoPercent = (player['2P%'] * 100).toFixed(1);
                const threePercent = (player['3P%'] * 100).toFixed(1);
                const made2Likelihood = player['Made 2 Likelihood (counts)'] !== undefined ? player['Made 2 Likelihood (counts)'].toFixed(1) : '0.0';
                const firstMadeWeighted = player['First Made (Weighted)'] || player['First Made'] || 'Unknown';
                
                // Determine color coding
                let fgClass = 'stat';
                if (player['FG%'] >= 0.50) fgClass += ' high-stat';
                else if (player['FG%'] < 0.40) fgClass += ' low-stat';
                else fgClass += ' medium-stat';
                
                row.innerHTML = `
                    <td><strong>${{rank}}</strong></td>
                    <td><strong>${{player.Player}}</strong></td>
                    <td><span class="stat-badge">${{player.Team}}</span></td>
                    <td class="${{fgClass}}">${{fgPercent}}%</td>
                    <td>${{twoPercent}}%</td>
                    <td>${{threePercent}}%</td>
                    <td><strong>${{made2Likelihood}}%</strong></td>
                    <td><strong>${{firstMadeWeighted}}</strong></td>
                `;
                tbody.appendChild(row);
            }});
            
            document.getElementById('resultInfo').textContent = `Showing ${{data.length}} of ${{allPlayers.length}} players`;
        }}
        
        // Filter table by team and player name
        function filterTable() {{
            const teamFilter = document.getElementById('teamFilter').value.toUpperCase();
            const playerSearch = document.getElementById('playerSearch').value.toLowerCase();
            
            currentData = allPlayers.filter(player => {{
                const teamMatch = teamFilter === '' || player.Team.toUpperCase() === teamFilter;
                const playerMatch = player.Player.toLowerCase().includes(playerSearch);
                return teamMatch && playerMatch;
            }});
            
            // When filtering by team, sort by rank ascending (best rank first)
            if (teamFilter !== '') {{
                currentData.sort((a, b) => a['Rank'] - b['Rank']);
            }}
            
            populateTable(currentData);
        }}
        
        // Reset filters
        function resetFilters() {{
            document.getElementById('teamFilter').value = '';
            document.getElementById('playerSearch').value = '';
            currentData = [...allPlayers];
            populateTable(currentData);
        }}
        
        // Sort table by column
        function sortTable(columnIndex) {{
            const headers = ['Rank', 'Player', 'Team', 'FG%', '2P%', '3P%', 'Made 2 Likelihood (counts)', 'First Made (Weighted)'];
            const sortKey = headers[columnIndex];
            const isAscending = sortAscending[columnIndex] || false;
            
            currentData.sort((a, b) => {{
                let aVal = a[sortKey];
                let bVal = b[sortKey];
                
                // Handle numeric sorting
                if (typeof aVal === 'number') {{
                    return isAscending ? aVal - bVal : bVal - aVal;
                }}
                
                // Handle string sorting
                const comparison = aVal.localeCompare(bVal);
                return isAscending ? comparison : -comparison;
            }});
            
            sortAscending[columnIndex] = !isAscending;
            populateTable(currentData);
        }}
        
        // Initialize table on page load
        window.onload = function() {{
            populateTable(allPlayers);
        }};
    </script>
</body>
</html>
"""
    
    return html_content


def save_html(html_content, filename="nba_stats.html"):
    """
    Save HTML content to file
    """
    filepath = Path(__file__).parent / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Interactive table saved to: {filepath}")
    return filepath


def main():
    """
    Main function to orchestrate the table creation
    """
    # Try to scrape all NBA players
    print("Attempting to scrape all NBA players from basketball-reference.com...")
    players_data = scrape_nba_stats()
    
    # If scraping fails, use sample data
    if players_data is None or len(players_data) == 0:
        print("Scraping failed or no data found. Using sample data...")
        players_data = create_sample_data()
    
    print(f"Loaded {len(players_data)} players")
    
    # Add calculated 'First Made' field
    players_data = add_first_made_calculation(players_data)
    
    # Get unique teams
    teams = sorted(set(p['Team'] for p in players_data))
    print(f"Teams: {', '.join(teams)}")
    
    # Sort by rank ascending (1 first) for default view
    players_data = sorted(players_data, key=lambda x: x.get('Rank', 999))
    
    # Create and save HTML
    html_content = create_interactive_html(players_data)
    filepath = save_html(html_content)
    
    # print(f"\n✅ Success! Open the HTML file in your browser to interact with the stats table.")
    # print(f"You can:")
    # print(f"  - Filter players by team")
    # print(f"  - Search for specific players")
   #  print(f"  - Click column headers to sort")
    print(f"  - View FG%, 2P%, and 3P% statistics")
    
    return players_data, filepath


if __name__ == "__main__":
    # Uncomment to scrape dunk stats
    # dunk_data = scrape_dunk_stats()
    # if dunk_data:
    #     print("\nDunk Stats Sample:")
    #     for p in dunk_data[:5]:
    #         print(p)
    
    players_data, filepath = main()
