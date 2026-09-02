import asyncio
import json
from core.mongodb import mongodb_connection

async def main():
    await mongodb_connection.connect()
    doc = await mongodb_connection.db.projects.find_one({}, sort=[('_id', -1)])
    if doc:
        report = doc.get('architecture_report', {})
        atlas = report.get('atlas_executive', {})
        print(json.dumps(atlas, indent=2))
    else:
        print('No project found.')
    await mongodb_connection.close()

if __name__ == '__main__':
    asyncio.run(main())
