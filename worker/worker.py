import os,time,boto3,psycopg2
from io import BytesIO
from pypdf import PdfReader
from datetime import datetime,timezone
S3=boto3.client("s3",endpoint_url=os.getenv("S3_ENDPOINT_URL"),region_name=os.getenv("S3_REGION"),aws_access_key_id=os.getenv("S3_ACCESS_KEY"),aws_secret_access_key=os.getenv("S3_SECRET_KEY"))
SQS=boto3.client("sqs",endpoint_url=os.getenv("SQS_ENDPOINT_URL"),region_name=os.getenv("S3_REGION"),aws_access_key_id=os.getenv("S3_ACCESS_KEY"),aws_secret_access_key=os.getenv("S3_SECRET_KEY"))
Q=os.environ["SQS_QUEUE_URL"]; B=os.getenv("S3_BUCKET","docuflow"); DB=os.environ["DATABASE_URL"].replace("postgresql+psycopg2://","postgresql://")
while True:
 r=SQS.receive_message(QueueUrl=Q,MaxNumberOfMessages=5,WaitTimeSeconds=10,VisibilityTimeout=60)
 for m in r.get("Messages",[]):
  cid=int(m["Body"]); conn=psycopg2.connect(DB); cur=conn.cursor()
  try:
   cur.execute("select object_key from documents where id=%s",(cid,)); row=cur.fetchone()
   if not row: continue
   cur.execute("update documents set status='PROCESSING' where id=%s",(cid,)); conn.commit()
   data=S3.get_object(Bucket=B,Key=row[0])["Body"].read(); text=""
   if row[0].lower().endswith(".pdf"): text="\n".join((p.extract_text() or "") for p in PdfReader(BytesIO(data)).pages)
   else: text=data.decode("utf-8",errors="ignore")
   cur.execute("update documents set status='COMPLETED',extracted_text=%s where id=%s",(text[:500000],cid)); conn.commit()
  except Exception as e:
   cur.execute("update documents set status='FAILED',error_message=%s where id=%s",(str(e)[:4000],cid)); conn.commit()
  finally: cur.close(); conn.close(); SQS.delete_message(QueueUrl=Q,ReceiptHandle=m["ReceiptHandle"])
 time.sleep(1)
