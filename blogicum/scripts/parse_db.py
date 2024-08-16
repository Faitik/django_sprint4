from blog.models import Category, Location, Post, User
import sys
import os
import django
import json

# Set up Django environment
sys.path.append("../")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "blogicum.settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()


def delete_existing_data():
    """Delete all existing Category, Location, Post, and User data."""
    Category.objects.all().delete()
    Location.objects.all().delete()
    Post.objects.all().delete()
    User.objects.all().delete()


def create_instance(model_class, fields):
    """Create and save an instance of a model with given fields."""
    instance = model_class()
    m2m_fields = {}
    for key, value in fields.items():
        field = model_class._meta.get_field(key)
        if field.many_to_many:
            m2m_fields[key] = value
        else:
            setattr(instance, key, value)
    instance.save()

    # Handle ManyToMany fields after the instance has been saved
    for key, value in m2m_fields.items():
        getattr(instance, key).set(value)

    return instance


def process_data_by_model(data, model_name, model_class):
    """Process data for a specific model."""
    for row in data:
        if row["model"] == model_name:
            create_instance(model_class, row["fields"])


def process_posts(data):
    """Process and create Post instances with proper foreign keys."""
    for row in data:
        if row["model"] == "blog.post":
            post = Post()
            m2m_fields = {}
            for key, value in row["fields"].items():
                field = Post._meta.get_field(key)
                if field.many_to_many:
                    m2m_fields[key] = value
                elif key == "location":
                    value = Location.objects.get(id=value)
                elif key == "author":
                    value = User.objects.get(id=value)
                elif key == "category":
                    value = Category.objects.get(id=value)
                setattr(post, key, value)
            post.save()

            # Handle ManyToMany fields after the instance has been saved
            for key, value in m2m_fields.items():
                getattr(post, key).set(value)


def main():
    delete_existing_data()

    with open('db.json', 'r', encoding="utf-8") as file:
        data = json.load(file)

        # Process data in the desired order
        process_data_by_model(data, "blog.location", Location)
        process_data_by_model(data, "auth.user", User)
        process_data_by_model(data, "blog.category", Category)
        process_posts(data)

    print("Data processing complete.")


if __name__ == "__main__":
    main()
