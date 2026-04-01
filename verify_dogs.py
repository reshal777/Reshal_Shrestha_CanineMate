from pets.models import Dog
for d in Dog.objects.filter(is_adoptable=True):
    print(f"ID: {d.id}, Name: {d.name}, Image: {d.image}, Is Adoptable: {d.is_adoptable}")
