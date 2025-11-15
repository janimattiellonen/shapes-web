#!/usr/bin/env python3
"""
Quick test to verify the disc identification system is working.
Creates a simple test image if no image is provided.
"""

import sys
import requests
import json
from PIL import Image, ImageDraw, ImageFont
import io

API_URL = "http://localhost:8000"

def create_test_image():
    """Create a simple test disc image"""
    # Create a white circular disc
    img = Image.new('RGB', (500, 500), color='white')
    draw = ImageDraw.Draw(img)

    # Draw disc outline
    draw.ellipse([50, 50, 450, 450], outline='gray', width=3)

    # Add some text
    draw.text((250, 200), "Test Disc", fill='blue', anchor='mm')
    draw.text((250, 250), "Vanilla", fill='blue', anchor='mm')
    draw.text((250, 300), "STEADY", fill='blue', anchor='mm')

    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)

    return img_bytes

def test_system():
    """Run a quick system test"""
    print("\n" + "="*60)
    print("🥏 Disc Identification System - Quick Test")
    print("="*60 + "\n")

    # 1. Health check
    print("1️⃣  Checking system health...")
    try:
        response = requests.get(f"{API_URL}/discs/identification/health/check", timeout=5)
        health = response.json()
        print(f"   ✅ System is healthy!")
        print(f"   📊 Encoder: {health['encoder']}")
        print(f"   📐 Dimension: {health['encoder_dim']}")
    except requests.exceptions.ConnectionError:
        print("   ❌ Error: Cannot connect to API")
        print("   💡 Make sure backend is running: docker-compose up -d")
        return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    print("\n2️⃣  Creating test disc image...")
    test_img = create_test_image()
    print("   ✅ Test image created")

    # 2. Register disc
    print("\n3️⃣  Registering test disc...")
    try:
        files = {'image': ('test_disc.jpg', test_img, 'image/jpeg')}
        data = {
            'owner_name': 'Test User',
            'owner_contact': 'test@example.com',
            'disc_model': 'Test Vanilla',
            'disc_color': 'White',
            'notes': 'Auto-generated test disc'
        }
        response = requests.post(
            f"{API_URL}/discs/identification/register",
            files=files,
            data=data,
            timeout=60
        )
        result = response.json()
        print(f"   ✅ Disc registered!")
        print(f"   🆔 Disc ID: {result['disc_id']}")
        print(f"   🖼️  Image ID: {result['image_id']}")
        print(f"   🤖 Model: {result['model_used']}")
        disc_id = result['disc_id']
    except Exception as e:
        print(f"   ❌ Error: {e}")
        if 'response' in locals():
            print(f"   Response: {response.text}")
        return

    # 3. Search for same disc
    print("\n4️⃣  Searching for the disc...")
    test_img.seek(0)  # Reset file pointer
    try:
        files = {'image': ('test_disc.jpg', test_img, 'image/jpeg')}
        data = {'top_k': '5', 'min_similarity': '0.5'}
        response = requests.post(
            f"{API_URL}/discs/identification/search",
            files=files,
            data=data,
            timeout=60
        )
        result = response.json()
        print(f"   ✅ Search complete!")
        print(f"   📊 Found {result['total_matches']} matches")

        if result['matches']:
            best_match = result['matches'][0]
            similarity = best_match['similarity']
            print(f"\n   🏆 Best Match:")
            print(f"      Similarity: {similarity:.2%}")
            print(f"      Disc ID: {best_match['disc_id']}")
            print(f"      Model: {best_match['disc_model']}")

            if similarity > 0.95:
                print(f"\n   ✨ Excellent! High similarity means the system is working perfectly!")
            elif similarity > 0.7:
                print(f"\n   👍 Good match! System is working correctly.")
            else:
                print(f"\n   🤔 Low similarity - this might indicate an issue.")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return

    # 4. Get disc info
    print(f"\n5️⃣  Getting disc information...")
    try:
        response = requests.get(f"{API_URL}/discs/identification/{disc_id}", timeout=5)
        result = response.json()
        print(f"   ✅ Disc info retrieved!")
        print(f"      Owner: {result['owner_name']}")
        print(f"      Status: {result['status']}")
        print(f"      Images: {len(result['images'])}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    print("\n" + "="*60)
    print("✅ Test Complete!")
    print("="*60)
    print(f"\n💡 Next steps:")
    print(f"   • Try with your real disc image:")
    print(f"     python3 test_disc.py ~/Downloads/your_disc.jpg")
    print(f"   • View API docs: {API_URL}/docs")
    print(f"   • Check database: docker exec -it shapes-postgres psql -U postgres -d disc_identification")
    print()

if __name__ == "__main__":
    test_system()
