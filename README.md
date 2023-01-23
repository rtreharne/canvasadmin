# django-docker-compose-deployment

This is a template dockerised Django project configured for use with:

+ PostgreSQL
+ Nginx for file serving
+ Celery, Beat and Redis

Guidance on build for both local development and production (Amazon AWS EC2) below.

## Guidance

### Step 1. Clone repo

```bash
git clone git@github.com:rtreharne/django-docker-compose-deployment.git
```

If you need to configure your ssh key then read <a href="https://docs.github.com/en/authentication/connecting-to-github-with-ssh/adding-a-new-ssh-key-to-your-github-account" target="_blank">this</a>.

### Step 2 - Install Docker

Linux (Ubbuntu 22.04):

https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-22-04

Windows:

https://statswork.wiki/docker-for-windows/install-windows-home/

### Step 3 - Build image and run in container locally

```bash
docker-compose build app
```

```bash
docker-compose up app
```
To check open up http://127.0.0.1:8000/

If you want to stop and remove your container later then:
```bash
docker-compose down
```
*This will destroy your local database!

### Step 4 - Create a superuser
```bash
docker-compose run --rm app sh -c "python manage.py createsuperuser"
```
Run `docker-compose up app` again and navigate to `/admin` to login to Django admin.

### Step 5 - Make sure your beat scheduler is running

This command creates a new container to run in the background.

```bash
docker-compose run -d --rm app sh -c "celery -A app beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler"
```

### Step 5 - Development

Develop your app locally. Your changes should be reflected on your local server

### Step 6 - Test deployment locally

### Step 7 - Deploy to AWS EC2




