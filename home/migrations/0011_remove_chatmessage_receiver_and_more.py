from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("home", "0010_product_discount_percent_product_old_price"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(model_name="chatmessage", name="receiver"),
                migrations.RemoveField(model_name="chatmessage", name="sender"),
                migrations.RemoveField(model_name="veterinarian", name="clinic"),
                migrations.RemoveField(model_name="dog", name="owner"),
                migrations.RemoveField(model_name="medication", name="dog"),
                migrations.RemoveField(model_name="groomingbooking", name="dog"),
                migrations.RemoveField(model_name="vaccination", name="dog"),
                migrations.RemoveField(model_name="healthrecord", name="dog"),
                migrations.RemoveField(model_name="groomingbooking", name="salon"),
                migrations.RemoveField(model_name="groomingbooking", name="service"),
                migrations.RemoveField(model_name="groomingbooking", name="user"),
                migrations.RemoveField(model_name="order", name="product"),
                migrations.RemoveField(model_name="order", name="user"),
                migrations.RemoveField(model_name="veterinarian", name="user"),
                migrations.DeleteModel(name="Appointment"),
                migrations.DeleteModel(name="ChatMessage"),
                migrations.DeleteModel(name="Clinic"),
                migrations.DeleteModel(name="Medication"),
                migrations.DeleteModel(name="Vaccination"),
                migrations.DeleteModel(name="Dog"),
                migrations.DeleteModel(name="HealthRecord"),
                migrations.DeleteModel(name="GroomingSalon"),
                migrations.DeleteModel(name="GroomingService"),
                migrations.DeleteModel(name="GroomingBooking"),
                migrations.DeleteModel(name="Product"),
                migrations.DeleteModel(name="Order"),
                migrations.DeleteModel(name="Veterinarian"),
            ],
            database_operations=[]
        )
    ]
