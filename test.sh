if [ "$1" = "localhost" ]; then
  python /Users/poorvikd/Documents/CloudComp/CSE546-Cloud-Computing/workload_generator/workload_generator.py --num_request $2 --url 'http://127.0.0.1:8000/' --image_folder "/Users/poorvikd/Documents/CloudComp/CSE546-Cloud-Computing/dataset/face_images_1000" --prediction_file "/Users/poorvikd/Documents/CloudComp/CSE546-Cloud-Computing/dataset/Classification Results on Face Dataset (1000 images).csv"
fi

if [ "$1" = "ec2" ]; then
  python /Users/poorvikd/Documents/CloudComp/CSE546-Cloud-Computing/workload_generator/workload_generator.py --num_request $2 --url 'http://100.24.155.186/' --image_folder "/Users/poorvikd/Documents/CloudComp/CSE546-Cloud-Computing/dataset/face_images_1000" --prediction_file "/Users/poorvikd/Documents/CloudComp/CSE546-Cloud-Computing/dataset/Classification Results on Face Dataset (1000 images).csv"
fi