import boto3
from botocore.exceptions import ClientError
from botocore.client import Config
import click
import os
import time
import zipfile

@click.command()
@click.option('--profile', default='default',
    help="AWS Profile to use")
@click.option('--bucket', help="S3 bucket to use")
@click.option('--project', default='BuildMemealator',
    help="CodeBuild project to use")
@click.option('--function', default='memealator_make_meme',
    help="Lambda function to update")
def build(profile, bucket, project, function):
    """Build memealator"""
    session = boto3.Session(profile_name=profile)

    # Zip it
    with zipfile.ZipFile('memealator-source.zip', 'w') as zf:
        zf.write('buildspec.yml')
        zf.write('Pipfile')
        zf.write('setup.py')
        zf.write('memeify/')
        for f in [os.path.join('memeify', f) for f in os.listdir('memeify') if os.path.isfile(os.path.join('memeify', f))]:
            zf.write(f)

    # Upload to S3
    s3 = session.resource('s3', config=Config(signature_version='s3v4'))
    s3_bucket = s3.Bucket(bucket)
    s3_bucket.upload_file('memealator-source.zip', 'memealator-source.zip')

    # Start build
    cb = session.client('codebuild')
    build = cb.start_build(projectName=project)

    build_id = build['build']['id']
    build_status = build['build']['buildStatus']
    print(build_id)

    while build_status == 'IN_PROGRESS':
        time.sleep(5)
        build_status = cb.batch_get_builds(ids=[build_id])['builds'][0]['buildStatus']
        print(build_status)

    # Update lambda function
    l = session.client('lambda')
    l.update_function_code(
        FunctionName=function,
        S3Bucket=bucket,
        S3Key='BuildMemalatyr/dist/memealator_9000-0.1.zip')


if __name__ == '__main__':
    build()
