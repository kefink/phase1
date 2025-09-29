"""
Utility to construct a SQLAlchemy DATABASE_URL for MySQL (Aiven, RDS, etc.)
Ensures the password is URL-encoded correctly for special characters.

Usage:
  python scripts/build_database_url.py --user USER --password 'P@ss w/rd' \
      --host my-aiven-host --port 12345 --db hillview_demo001

Output:
  mysql+pymysql://USER:ENCODED_PASSWORD@HOST:PORT/DB?charset=utf8mb4
"""
import argparse
from urllib.parse import quote_plus

parser = argparse.ArgumentParser(description="Build MySQL SQLAlchemy DATABASE_URL")
parser.add_argument('--user', required=True)
parser.add_argument('--password', required=True)
parser.add_argument('--host', required=True)
parser.add_argument('--port', type=int, default=3306)
parser.add_argument('--db', required=True)
args = parser.parse_args()

encoded = quote_plus(args.password)
url = f"mysql+pymysql://{args.user}:{encoded}@{args.host}:{args.port}/{args.db}?charset=utf8mb4"
print(url)
