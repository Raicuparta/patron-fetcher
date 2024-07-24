import json
import urllib.request
import urllib.error
import argparse


def parse_args():
    parser = argparse.ArgumentParser(description='Patreon API Client')
    parser.add_argument('--access-token', required=True,
                        help='Patreon API access token')
    return parser.parse_args()


def fetch_data(url, access_token):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    })

    try:
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                raise Exception(
                    f"Failed to fetch data: {response.status} {response.reason}")
            return json.load(response)
    except urllib.error.URLError as e:
        raise Exception(f"Failed to fetch data: {e.reason}")


def process_data(data):
    patrons = []

    # filtered by type user
    users = data.get('included', [])

    for item in data.get('data', []):
        user = next(
            (u for u in users if u['id'] == item['relationships']['user']['data']['id']), None)
        if user is None:
            continue

        user_attributes = user.get('attributes', {})

        data_attributes = item.get('attributes', {})
        if data_attributes.get('patron_status') != 'active_patron':
            continue

        if user_attributes.get('hide_pledges'):
            continue

        patrons.append({
            "data": data_attributes,
            "user": user_attributes
        })
    return patrons


def fetch_all_patrons(url, access_token):
    patrons = []
    while url:
        data = fetch_data(url, access_token)
        patrons.extend(process_data(data))
        url = data.get('links', {}).get('next')
    return patrons


def save_to_file(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)


def main():
    args = parse_args()
    base_url = ("https://www.patreon.com/api/oauth2/v2/campaigns/7004713/members"
                "?include=user"
                "&fields%5Bmember%5D=full_name,patron_status,campaign_lifetime_support_cents"
                "&fields%5Buser%5D=thumb_url,hide_pledges,vanity"
                "&page%5Bcount%5D=1000")
    patrons = fetch_all_patrons(base_url, args.access_token)
    sorted_patrons = sorted(
        patrons, key=lambda x: x['data']['campaign_lifetime_support_cents'], reverse=True)
    result = {"activePatrons": [{
        "ranking": i + 1,
        "name": p['user']['vanity'] or p['data']['full_name'],
        "imageUrl": p['user']['thumb_url']
    } for i, p in enumerate(sorted_patrons)]}
    save_to_file("patrons.json", result)
    print("Patrons data saved to patrons.json")


if __name__ == "__main__":
    main()
