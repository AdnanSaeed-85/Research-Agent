from CONFIG import S3, BUCKET
from langsmith import traceable

@traceable('upload pdf on s3')
def upload_pdf(file_path, file_name):
    """Upload PDF to S3"""
    S3.upload_file(file_path, BUCKET, file_name)
    return f"s3://{BUCKET}/{file_name}"

@traceable('download pdf from s3')
def download_pdf(file_name, save_path):
    """Download PDF from S3"""
    S3.download_file(BUCKET, file_name, save_path)
    return save_path

# Usage:
upload_pdf('A:\Agent_PDF\AI_Agents.pdf', 'AI_Agents.pdf')
download_pdf('AI_Agents.pdf', 'AI_Agent.pdf')