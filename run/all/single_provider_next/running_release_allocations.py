import os


def get_current_directory_name():
    path = (os.path.dirname(os.path.realpath(__file__)))
    return os.path.split(path)[1]


dir_name = get_current_directory_name()
docker_name_req = f"{dir_name}-yagna_req-1"
print(f"docker_name: {docker_name_req}")
command = f"docker exec -it {docker_name_req} yagna payment release-allocations"

print(f"exec: {command}")
os.system(command)