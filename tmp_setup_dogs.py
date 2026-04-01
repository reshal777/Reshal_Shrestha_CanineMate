from pets.models import Dog
dogs = Dog.objects.all()[:6]
locations = ['Pokhara Lakeside', 'Lalitpur', 'Bhaktapur', 'Pokhara', 'Kathmandu', 'Patan']
descriptions = [
    "Friendly and energetic, great with kids",
    "Sweet and gentle, loves to play",
    "Well-trained, good with other dogs",
    "Playful puppy looking for a loving home",
    "Active and adventurous, needs space to run",
    "Small and adorable, perfect for apartments"
]
for i, d in enumerate(dogs):
    d.is_adoptable = True
    d.location = locations[i % len(locations)]
    d.description = descriptions[i % len(descriptions)]
    d.is_vaccinated = True
    d.save()
print(f"Updated {dogs.count()} dogs to be adoptable.")
