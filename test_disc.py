#!/usr/bin/env python3
"""
Test script for disc identification system
Usage: python3 test_disc.py <path_to_disc_image>
"""

import sys
import requests
import json
from pathlib import Path

API_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60 + "\n")

def health_check():
    """Test health endpoint"""
    print_section("1. Health Check")
    response = requests.get(f"{API_URL}/discs/identification/health/check")
    print(json.dumps(response.json(), indent=2))
    return response.json()

def register_disc(image_path):
    """Register a disc"""
    print_section("2. Registering Disc")

    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {
            'owner_name': 'Test User',
            'owner_contact': 'test@example.com',
            'disc_model': 'Clash Vanilla',
            'disc_color': 'White',
            'notes': 'Distance driver - steady flight'
        }
        response = requests.post(
            f"{API_URL}/discs/identification/register",
            files=files,
            data=data
        )

    result = response.json()
    print(json.dumps(result, indent=2))
    return result

def search_disc(image_path):
    """Search for matching discs"""
    print_section("3. Searching for Matches")

    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {
            'top_k': '5',
            'min_similarity': '0.5'
        }
        response = requests.post(
            f"{API_URL}/discs/identification/search",
            files=files,
            data=data
        )

    result = response.json()
    print(json.dumps(result, indent=2))

    # Print summary
    if result['matches']:
        print("\n📊 Match Summary:")
        for i, match in enumerate(result['matches'], 1):
            print(f"  {i}. Similarity: {match['similarity']:.2%} - {match['disc_model']} ({match['status']})")
    else:
        print("\n❌ No matches found")

    return result

def get_disc_info(disc_id):
    """Get disc information"""
    print_section("4. Disc Information")

    response = requests.get(f"{API_URL}/discs/identification/{disc_id}")
    result = response.json()
    print(json.dumps(result, indent=2))
    return result

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 test_disc.py <path_to_disc_image>")
        print("Example: python3 test_disc.py ~/Downloads/disc.jpg")
        sys.exit(1)

    image_path = Path(sys.argv[1])

    if not image_path.exists():
        print(f"❌ Error: Image file not found: {image_path}")
        sys.exit(1)

    print(f"\n🥏 Testing Disc Identification System")
    print(f"📸 Image: {image_path}")

    try:
        # 1. Health check
        health = health_check()
        print(f"✅ System healthy - Using {health['encoder']} encoder")

        # 2. Register disc
        registration = register_disc(image_path)
        disc_id = registration['disc_id']
        print(f"✅ Disc registered with ID: {disc_id}")

        # 3. Search for disc
        search_results = search_disc(image_path)
        print(f"✅ Found {search_results['total_matches']} matches")

        # 4. Get disc info
        disc_info = get_disc_info(disc_id)
        print(f"✅ Retrieved disc information")

        print_section("✨ Test Complete!")
        print(f"🎯 Disc ID: {disc_id}")
        print(f"🔍 API Docs: {API_URL}/docs")
        print(f"💾 Database: localhost:5440")

        if search_results['matches']:
            best_match = search_results['matches'][0]
            print(f"\n🏆 Best Match: {best_match['similarity']:.2%} similarity")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Cannot connect to API")
        print("Make sure the backend is running: docker-compose up -d")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
