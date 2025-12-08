from jobsai.main import main


def handler(event, context):
    main(event["form_submissions"])
