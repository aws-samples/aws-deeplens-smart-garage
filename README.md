## Smart-Garage

This repository is part of a blog post that guides users through creating a License Plate recognization system to open the garage door which uses object detection model using AWS DeepLens

Following the steps described in the blog post, the final architecture is this:

![diagram](../master/architecture.png)

### *License-Plate-Match-cloud.py*
Using Amazon Rekognition, this lambda function responsible for recognising a License Plate, and match the plate number with DynamoDB. If match found then it will call the myq.py module to call 3rd party api to open the garage door

### *deeplens_lambda.py*
This lambda function runs on the AWS DeepLens and perform inferences and the necessary logic. It uploads frames on every 30 sec to Amazon S3 when a car is detected.


## License

This library is licensed under the MIT-0 License. See the LICENSE file.


