# import time

# from app.db import SessionLocal
# from app.routes.crawl_jobs import run_one_crawl_job


# def main():
#     print("Crawl worker started")

#     while True:
#         db = SessionLocal()

#         try:
#             result = run_one_crawl_job(db=db)
#             print(result)

#         except Exception as error:
#             print(f"[ERROR] {error}")

#         finally:
#             db.close()

#         time.sleep(5)


# if __name__ == "__main__":
#     main()

import time

from app.db import SessionLocal
from app.services.crawl_job_runner import process_one_crawl_job


def main():
    print("Crawl worker started")

    while True:
        db = SessionLocal()

        try:
            result = process_one_crawl_job(db)
            print(result)

        except Exception as error:
            print(f"[ERROR] {error}")

        finally:
            db.close()

        time.sleep(5)


if __name__ == "__main__":
    main()