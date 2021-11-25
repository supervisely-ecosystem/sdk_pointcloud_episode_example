import sys

sys.path.append('/sly')
import supervisely_lib as sly
from supervisely_lib.geometry.cuboid_3d import Cuboid3d, Vector3d
from supervisely_lib.pointcloud_annotation.pointcloud_object_collection import PointcloudObjectCollection
from supervisely_lib.pointcloud_annotation.pointcloud_figure import PointcloudFigure
from supervisely_lib.video_annotation.key_id_map import KeyIdMap
from supervisely_lib.api.module_api import ApiField


# Initialize API object
SERVER_ADDRESS = "SERVER ADDRESS"
API_TOKEN = "YOUR TOKEN"
WORKSPACE_ID = 320  # your workspace id

api = sly.Api(SERVER_ADDRESS, API_TOKEN)


"""
STEP 1 — Create project
"""

project_name = 'demo_episode_project'
sequence_name = 'demo_sequence'

project = api.project.create(WORKSPACE_ID, project_name, type=sly.ProjectType.POINT_CLOUD_EPISODES, change_name_if_conflict=True)
sequence = api.dataset.create(project.id, f'{sequence_name}', change_name_if_conflict=True)

# Update project classes
class_car = sly.ObjClass('car', Cuboid3d)  # class name, figure type
class_pedestrian = sly.ObjClass('pedestrian', Cuboid3d)
classes = sly.ObjClassCollection([class_car, class_pedestrian])  # define two classes in our project
project_meta = sly.ProjectMeta(classes)
updated_meta = api.project.update_meta(project.id, project_meta.to_json())



"""
STEP 1 — Upload frames (pointclouds) to sequence
"""

first_pointcloud_path = "my_clouds/001.pcd"  # path to .pcd file
first_pointcloud_name = "001.pcd"  # file name (with .pcd extension)
first_frame_idx = 0  # index of frame in sequence for sorting in timeline
first_pointcloud = api.pointcloud_episode.upload_path(sequence.id,
                                                      first_pointcloud_name,
                                                      first_pointcloud_path,
                                                      {"frame": first_frame_idx})

second_pointcloud_path = "my_clouds/002.pcd"
second_pointcloud_name = "002.pcd"
second_frame_idx = 1
second_pointcloud = api.pointcloud_episode.upload_path(sequence.id,
                                                       second_pointcloud_name,
                                                       second_pointcloud_path,
                                                       {"frame": second_frame_idx})


"""
STEP 2 — Upload photo context and attach it to frame

Using bulk upload method. 
At first we load all images to server and get hashes from it.
Next we attach images with theirs META to pointclouds in sequence

"""

list_of_img_paths = ["my_photos/001/photo1.jpeg"]
image_meta = {
        "deviceId": "CAM_FRONT",  # some custom id to link cameras between frames
        "timestamp": "2019-01-11T03:24:12.001Z",
        "sensorsData": {
            "extrinsicMatrix": [-0.050929406593937084, 0.9986867060614835, -0.005573031495827873, -0.03365781352785508,
                                0.010643679582592826, -0.005037184119239299, -0.9999306670270152, -0.13933063818038205,
                                -0.9986455365288186, -0.050985193068310834, -0.010373160504616235, 0.34260511837557783],
            "intrinsicMatrix": [882.616669855, 0,             606.762205915,
                                0,             882.616669855, 519.507109885,
                                0,             0,             1]
        }
}

hashes = api.pointcloud_episode.upload_related_images(list_of_img_paths)  # upload images to server using bulk method
hash = hashes[0]  # get first hash from list, because we upload only 1 photo

image_infos = [{ApiField.ENTITY_ID: first_pointcloud.id,  # id to which point cloud the image will be attached
                ApiField.NAME: "photo1.jpeg",  # some unique image name
                ApiField.HASH: hash,
                ApiField.META: image_meta}]


api.pointcloud_episode.add_related_images(image_infos)  # attach images to pointcloud



"""
STEP 3 — Creating objects 

Creating 3 object on 2 frames.
- One pedestrian object 
- Two cars objects 
"""

key_id_map = KeyIdMap()  # creating this helper object to link objects and figures

pedestrian_object = sly.PointcloudObject(class_pedestrian)
first_car_object = sly.PointcloudObject(class_car)
second_car_object = sly.PointcloudObject(class_car)

# merge all defined objects in sequence and upload it to sequence ('demo_sequence')
objects_collection = PointcloudObjectCollection([pedestrian_object, first_car_object, second_car_object])
uploaded_objects_ids = api.pointcloud_episode.object.append_to_dataset(sequence.id, objects_collection, key_id_map)


"""
STEP 4 — Creating figures
 
Creating 5 figures on 2 frames.
- One pedestrian figure on frame 0
- Figures for cars on first and second frames (4 figures, i.e. 2 figure for every car object (1 on frame))
"""
# here is random box size and position values givnen for example

# pedestrian figure
position, rotation, dimension = Vector3d(-32.4, 33.9, -0.7), Vector3d(0., 0, 0.1), Vector3d(1.8, 3.9, 1.6)
cuboid = Cuboid3d(position, rotation, dimension)
figure0 = PointcloudFigure(pedestrian_object, cuboid)  # Figure is bound to pedestrian object

api.pointcloud_episode.figure.append_bulk(first_pointcloud.id, [figure0], key_id_map)  # upload figure to pointcloud

# Car figures
position, rotation, dimension = Vector3d(-3.4, 30.9, -0.7), Vector3d(0., 0, 0.1), Vector3d(1.8, 3.9, 1.6)
cuboid = Cuboid3d(position, rotation, dimension)
figure1 = PointcloudFigure(first_car_object, cuboid)  # Figure is bound to first car object and will be placed to first frame

position, rotation, dimension = Vector3d(-3.4, 28.9, -0.7), Vector3d(0., 0, -0.03), Vector3d(1.8, 3.9, 1.6)
cuboid = Cuboid3d(position, rotation, dimension)
figure2 = PointcloudFigure(first_car_object, cuboid)  # Figure is bound to first car object and will be placed to second frame

position, rotation, dimension = Vector3d(-3.4, 23.9, -0.7), Vector3d(0., 0, 0.4), Vector3d(1.8, 3.9, 1.6)
cuboid = Cuboid3d(position, rotation, dimension)
figure3 = PointcloudFigure(second_car_object, cuboid)  # Figure is bound to second car object  and will be placed to first frame

position, rotation, dimension = Vector3d(-6.3, 23.9, -0.7), Vector3d(0., 0, -1.0), Vector3d(1.8, 3.9, 1.6)
cuboid = Cuboid3d(position, rotation, dimension)
figure4 = PointcloudFigure(second_car_object, cuboid)  # Figure is bound to second car object and will be placed to second frame


figures = [figure1, figure2, figure3, figure4]
# create an array of point cloud IDs according to their cuboids.
# i.e. figure1 on first pointcloud, figure4 on second pointcloud.
pointcloud_ids = [first_pointcloud.id, second_pointcloud.id, first_pointcloud.id, second_pointcloud.id]

api.pointcloud_episode.figure.append_to_dataset(sequence.id, figures, pointcloud_ids, key_id_map)



"""
 STEP 5 — Download pointclouds and photo-context
"""

# returns dict with frame_id and name of pointcloud by sequnce (dataset) id
frame_to_name_map = api.pointcloud_episode.get_frame_name_map(sequence.id)
# >> {0: '001', 1: '002'}

# way to get more info
clouds_info = api.pointcloud_episode.get_list(sequence.id)
# >> PointCloudInfo(id=2394445, frame=0, description='', name='001' ...
# >> PointCloudInfo(id=2394446, frame=1, description='', name='002'


# using pointcloud ids from info we can download the clouds
api.pointcloud_episode.download_path(clouds_info[0].id, "downloaded_pointcloud.pcd")

# find related to pointcloud photo-context images
images_info = api.pointcloud_episode.get_list_related_images(clouds_info[0].id)
# >> [{'id': 77250, 'name': 'photo1.jpeg', 'meta': {'deviceId': 'CAM_FRONT', 'timestamp': '2019-01 ...} ... }]
image_name = images_info[0][ApiField.NAME]
image_id = images_info[0][ApiField.ID]
# And download this images by theirs ids
api.pointcloud_episode.download_related_image(image_id, image_name)


"""
 STEP 6 — Download sequence annotation in json format
"""

ann_json = api.pointcloud_episode.annotation.download(sequence.id)
# >>> {'datasetId': 42936 ... 'objects': [{'id': 609701, ...], 'figures': [{'id': 57130832,
#      ... 'geometry': {'position': {'x': -32.4, 'y': 33.9, 'z': -0.7}...}] ...

# save json annotation to file
annotation_file = 'annotation.json'
sly.json.dump_json_file(ann_json, annotation_file)


"""
 STEP 7 — Some high-level methods
"""

from supervisely_lib.project.pointcloud_episode_project import download_pointcloud_episode_project, \
                                                               upload_pointcloud_episode_project


downloaded_project_dir = "downloaded_project"
# Download whole project or sequence (can be selected by list of seuqence_ids in dataset_ids parameter)
download_pointcloud_episode_project(api, project.id, downloaded_project_dir, dataset_ids=None,
                                        download_pcd=True,
                                        download_realated_images=True,
                                        download_annotations=True,
                                        log_progress=True)


# Upload whole project
upload_pointcloud_episode_project(downloaded_project_dir, api, WORKSPACE_ID,
                                  project_name="My_new_project",
                                  log_progress=True)
