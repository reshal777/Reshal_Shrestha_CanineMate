from pets.models import Dog
import os
with open('verify_results.txt', 'w') as f:
    for d in Dog.objects.filter(is_adoptable=True):
        f.write(f"ID: {d.id}, Name: {d.name}, Image: {d.image.url if d.image else 'EMPTY'}, Is Adoptable: {d.is_adoptable}\n")
print("Done writing results")
