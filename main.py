from fastapi import FastAPI, HTTPException, File, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import boto3
import time
import uuid
# from autoscaler import autoscale


SQS_REQUEST = 'https://sqs.us-east-1.amazonaws.com/474668424004/1229658367-req-queue'
SQS_RESPONSE = 'https://sqs.us-east-1.amazonaws.com/474668424004/1229658367-resp-queue'
S3_REQUEST = '1229658367-in-bucket'

origins = ["*"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/hello")
async def root():
    return {"message": "Hello World"}

@app.post('/')
async def get_face(inputFile: UploadFile = File(...)):


    file = inputFile.filename
    filename = inputFile.filename.split('.')[0]

    sqs = boto3.client('sqs')  

    s3 = boto3.client('s3')

    ec2 = boto3.client('ec2')

    # autoscale(sqs, ec2)

    try:
        s3.upload_fileobj(inputFile.file, S3_REQUEST, inputFile.filename)
        print(f"File {filename} uploaded to {S3_REQUEST}")
    except Exception as e:
        raise HTTPException(status_code=404, detail="Error uploading file to S3. "+str(e))

    img_uuid = str(uuid.uuid4())
    message = file+":"+img_uuid
    try:
        sqs.send_message(
            QueueUrl=SQS_REQUEST,
            MessageBody=message,
        )
        print(f"Message sent to {SQS_REQUEST}")
    except Exception as e:
        print(f"Error sending message "+str(e))
        raise HTTPException(status_code=404, detail="Error sending message to SQS. "+str(e))


    # fetch response from SQS
    response = None
    while not response:
        response = get_response_from_sqs(sqs, img_uuid)
        time.sleep(2)

    # autoscale(sqs, ec2)
    return PlainTextResponse(status_code=200, content = filename+":"+response)



def get_response_from_sqs(sqs, im_uuid):
    """Retrieve the response from SQS."""
    response = sqs.receive_message(
        QueueUrl=SQS_RESPONSE,
        AttributeNames=['All'],
        MaxNumberOfMessages=10,
        MessageAttributeNames=['All'],
        VisibilityTimeout=1,
        WaitTimeSeconds=5
    )
    message = response.get('Messages', [])

    if not message:
        return None

    for message in message:
        receipt_handle = message['ReceiptHandle']
        body = message['Body']
        face = body.split(":")[0]
        img_uuid = body.split(":")[1]

        if img_uuid == im_uuid:
            sqs.delete_message(
                QueueUrl=SQS_RESPONSE,
                ReceiptHandle=receipt_handle
            )
            return face

    return None