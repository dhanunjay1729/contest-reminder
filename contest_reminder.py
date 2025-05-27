import requests
import json
from datetime import datetime, timedelta
import pytz
from dateutil import parser

# Direct API endpoints
CODEFORCES_API = "https://codeforces.com/api/contest.list"

def fetch_codeforces_contests():
    """Fetch contests directly from Codeforces API"""
    try:
        response = requests.get(CODEFORCES_API, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'OK':
            upcoming = []
            for contest in data['result']:
                if contest['phase'] == 'BEFORE':
                    upcoming.append({
                        'name': contest['name'],
                        'platform': 'CodeForces',
                        'start_time': datetime.fromtimestamp(contest['startTimeSeconds'], tz=pytz.UTC),
                        'duration_seconds': contest['durationSeconds'],
                        'url': f"https://codeforces.com/contests/{contest['id']}"
                    })
            return upcoming
        return []
    except Exception as e:
        print(f"Error fetching from Codeforces: {e}")
        return []

def generate_codechef_contests():
    """Generate CodeChef contest schedule - Every Wednesday at 8:00 PM IST"""
    contests = []
    local_tz = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(local_tz)
    
    # Find next Wednesday
    days_until_wednesday = (2 - current_time.weekday()) % 7
    if days_until_wednesday == 0 and current_time.hour >= 20:
        days_until_wednesday = 7
    
    # Generate contests for next 2 weeks
    for week in range(3):  # Check 3 weeks to ensure we get 2 weeks of contests
        next_wednesday = current_time + timedelta(days=days_until_wednesday + (week * 7))
        next_wednesday = next_wednesday.replace(hour=20, minute=0, second=0, microsecond=0)
        
        # Only include if within 2 weeks
        if (next_wednesday - current_time).days <= 14:
            contests.append({
                'name': f'CodeChef Starters {140 + week}',  # Approximate contest number
                'platform': 'CodeChef',
                'start_time': next_wednesday.astimezone(pytz.UTC),
                'duration_seconds': 10800,  # 3 hours
                'url': 'https://www.codechef.com/contests'
            })
    
    return contests

def generate_leetcode_contests():
    """Generate LeetCode contest schedule based on their fixed pattern"""
    contests = []
    local_tz = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(local_tz)
    
    # Weekly Contest - Every Sunday at 8:00 AM IST
    days_until_sunday = (6 - current_time.weekday()) % 7
    if days_until_sunday == 0 and current_time.hour >= 8:
        days_until_sunday = 7
    
    for week in range(3):  # Check 3 weeks
        next_weekly = current_time + timedelta(days=days_until_sunday + (week * 7))
        next_weekly = next_weekly.replace(hour=8, minute=0, second=0, microsecond=0)
        
        # Only include if within 2 weeks
        if (next_weekly - current_time).days <= 14:
            contest_num = 450 + week
            contests.append({
                'name': f'Weekly Contest {contest_num}',
                'platform': 'LeetCode',
                'start_time': next_weekly.astimezone(pytz.UTC),
                'duration_seconds': 5400,  # 1.5 hours
                'url': 'https://leetcode.com/contest/'
            })
    
    # Biweekly Contest - Every other Saturday at 8:00 PM IST
    next_biweekly = local_tz.localize(datetime(2025, 6, 7, 20, 0, 0))
    
    for i in range(2):  # Next 2 biweekly contests
        contest_date = next_biweekly + timedelta(days=14 * i)
        if contest_date > current_time and (contest_date - current_time).days <= 14:
            contest_num = 131 + i
            contests.append({
                'name': f'Biweekly Contest {contest_num}',
                'platform': 'LeetCode',
                'start_time': contest_date.astimezone(pytz.UTC),
                'duration_seconds': 5400,  # 1.5 hours
                'url': 'https://leetcode.com/contest/'
            })
    
    return contests

def get_contest_category(contest_date, current_date):
    """Determine contest category for color coding"""
    days_diff = (contest_date.date() - current_date.date()).days
    
    if days_diff == 0:
        return "TODAY"
    elif days_diff <= 7:
        return "THIS_WEEK"
    elif days_diff <= 14:
        return "NEXT_WEEK"
    else:
        return "LATER"

def display_all_contests(all_contests):
    """Display all contests sorted by platform priority and time"""
    print("\n" + "="*70)
    print("UPCOMING PROGRAMMING CONTESTS (Next 2 Weeks)")
    print("="*70)
    
    if not all_contests:
        print("\nNo upcoming contests found.")
        return
    
    # Sort by platform priority (CodeForces, CodeChef, LeetCode) and then by time
    platform_priority = {'CodeForces': 1, 'CodeChef': 2, 'LeetCode': 3}
    all_contests.sort(key=lambda x: (platform_priority.get(x['platform'], 99), x['start_time']))
    
    local_tz = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(local_tz)
    current_platform = None
    
    # Color codes for terminal (will be used in GUI later)
    color_legend = {
        "TODAY": "🔴 [TODAY]",
        "THIS_WEEK": "🔵 [THIS WEEK]",
        "NEXT_WEEK": "🟢 [NEXT WEEK]"
    }
    
    print("\nLegend: 🔴 Today | 🔵 This Week | 🟢 Next Week\n")
    
    for contest in all_contests:
        # Filter contests beyond 2 weeks
        start_local = contest['start_time'].astimezone(local_tz)
        if (start_local - current_time).days > 14:
            continue
            
        if contest['platform'] != current_platform:
            current_platform = contest['platform']
            print(f"\n{'='*25} {current_platform} {'='*25}")
        
        # Calculate duration
        duration_seconds = int(contest['duration_seconds'])
        hours = duration_seconds // 3600
        minutes = (duration_seconds % 3600) // 60
        
        # Get category for color coding
        category = get_contest_category(start_local, current_time)
        color_indicator = color_legend.get(category, "")
        
        # Calculate time until contest
        time_diff = start_local - current_time
        days_until = time_diff.days
        
        print(f"\n📅 {contest['name']} {color_indicator}")
        print(f"   🕐 Start: {start_local.strftime('%A, %d %B %Y at %H:%M IST')}")
        
        if days_until == 0:
            hours_until = time_diff.seconds // 3600
            if hours_until == 0:
                print(f"   📌 Starting in {time_diff.seconds // 60} minutes!")
            else:
                print(f"   📌 TODAY in {hours_until} hours!")
        elif days_until == 1:
            print(f"   📌 Tomorrow")
        else:
            print(f"   📌 In {days_until} days")
            
        print(f"   ⏱️  Duration: {hours}h {minutes}m")
        print(f"   🔗 Link: {contest['url']}")
        print("-" * 70)

def main():
    print("Fetching contest data...")
    
    # Fetch from all platforms
    all_contests = []
    
    # Codeforces
    cf_contests = fetch_codeforces_contests()
    all_contests.extend(cf_contests)
    
    # CodeChef (generated from schedule)
    cc_contests = generate_codechef_contests()
    all_contests.extend(cc_contests)
    
    # LeetCode (generated from schedule)
    lc_contests = generate_leetcode_contests()
    all_contests.extend(lc_contests)
    
    # Display all contests
    display_all_contests(all_contests)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    local_tz = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(local_tz)
    
    platform_count = {}
    today_count = 0
    this_week_count = 0
    next_week_count = 0
    
    for contest in all_contests:
        start_local = contest['start_time'].astimezone(local_tz)
        if (start_local - current_time).days <= 14:
            platform = contest['platform']
            platform_count[platform] = platform_count.get(platform, 0) + 1
            
            category = get_contest_category(start_local, current_time)
            if category == "TODAY":
                today_count += 1
            elif category == "THIS_WEEK":
                this_week_count += 1
            elif category == "NEXT_WEEK":
                next_week_count += 1
    
    print("\nUpcoming contests by platform (next 2 weeks):")
    for platform in ['CodeForces', 'CodeChef', 'LeetCode']:
        count = platform_count.get(platform, 0)
        print(f"  • {platform}: {count} contests")
    
    print(f"\nBy timeline:")
    print(f"  🔴 Today: {today_count} contests")
    print(f"  🔵 This week: {this_week_count} contests")
    print(f"  🟢 Next week: {next_week_count} contests")
    
    # Find next contest
    if all_contests:
        # Filter to only show contests within 2 weeks
        valid_contests = [c for c in all_contests if (c['start_time'].astimezone(local_tz) - current_time).days <= 14]
        
        if valid_contests:
            next_contest = min(valid_contests, key=lambda x: x['start_time'])
            next_start = next_contest['start_time'].astimezone(local_tz)
            time_until = next_start - current_time
            
            print(f"\n⭐ Next Contest: {next_contest['name']} ({next_contest['platform']})")
            print(f"   Starts in: {time_until.days} days, {time_until.seconds//3600} hours")

if __name__ == "__main__":
    main()
