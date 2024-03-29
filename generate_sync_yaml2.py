import json
import os
import re
import yaml
import requests
from distutils.version import LooseVersion

# 基本配置
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, 'config2.yaml')
SYNC_FILE = os.path.join(BASE_DIR, 'sync2.yaml')



def is_exclude_tag(tag):
    """
    排除tag
    :param tag:
    :return:
    """
    excludes = ['alpha', 'beta', 'rc', 'amd64', 'ppc64le', 'arm64', 'arm', 's390x', 'SNAPSHOT', 'debug', 'master', 'latest', 'main']

    for e in excludes:
        if e.lower() in tag.lower():
            return True
        if str.isalpha(tag):
            return True
        if len(tag) >= 40:
            return True

    # 处理带有 - 字符的 tag
    if re.search("-\d$", tag, re.M | re.I):
        return False
    if '-' in tag:
        return False

    return False


def get_repo_aliyun_tags(image):
    """
    获取 aliyuncs repo 最新的 tag
    :param image:
    :return:
    """
    image_name = image.split('/')[-1]
    tags = []

    hearders = {
        'User-Agent': 'docker/19.03.12 go/go1.13.10 git-commit/48a66213fe kernel/5.8.0-1.el7.elrepo.x86_64 os/linux arch/amd64 UpstreamClient(Docker-Client/19.03.12 \(linux\))'
    }
    token_url = "https://dockerauth.cn-hangzhou.aliyuncs.com/auth?scope=repository:bitnano/{image}:pull&service=registry.aliyuncs.com:cn-guangzhou:26842".format(
        image=image_name)
    try:
        token_res = requests.get(url=token_url, headers=hearders)
        token_data = token_res.json()
        access_token = token_data['token']
    except Exception as e:
        print('[Get repo token]', e)
        return tags

    tag_url = "https://registry.cn-guangzhou.aliyuncs.com/v2/bitnano/{image}/tags/list".format(image=image_name)
    hearders['Authorization'] = 'Bearer ' + access_token

    try:
        tag_res = requests.get(url=tag_url, headers=hearders)
        tag_data = tag_res.json()
        print('[aliyun tag]: ', tag_data)
    except Exception as e:
        print('[Get tag Error]', e)
        return tags

    tags = tag_data.get('tags', [])
    return tags


def get_repo_gcr_tags(image, limit=5, host="registry.k8s.io"):
    """
    获取 gcr.io repo 最新的 tag
    :param host:
    :param image:
    :param limit:
    :return:
    """
    tag_url = "https://{host}/v2/{image}/tags/list".format(host=host, image=image)

    tags = []
    tags_data = []
    manifest_data = []

    try:
        tag_rep = requests.get(url=tag_url)
        tag_req_json = tag_rep.json()
        manifest_data = tag_req_json['manifest']
    except Exception as e:
        print('[Get tag Error]', e)
        return tags

    for manifest in manifest_data:
        sha256_data = manifest_data[manifest]
        sha256_tag = sha256_data.get('tag', [])
        if len(sha256_tag) > 0:
            # 排除 tag
            if is_exclude_tag(sha256_tag[0]):
                continue
            tags_data.append({
                'tag': sha256_tag[0],
                'timeUploadedMs': sha256_data.get('timeUploadedMs')
            })
    tags_sort_data = sorted(tags_data, key=lambda i: i['timeUploadedMs'], reverse=True)

    # limit tag
    tags_limit_data = tags_sort_data[:limit]

    for t in tags_limit_data:
        tags.append(t['tag'])
    # image_aliyun_tags = get_repo_aliyun_tags(image)
    # for t in tags_limit_data:
    #     # 去除同步过的
    #     if t['tag'] in image_aliyun_tags:
    #         continue

    #     tags.append(t['tag'])

    # print('[repo tag]', tags)
    return tags


def get_repo_quay_tags(image, limit=5):
    """
    获取 quay.io repo 最新的 tag
    :param image:
    :param limit:
    :return:
    """
    tag_url = "https://quay.io/api/v1/repository/{image}/tag/?onlyActiveTags=true&limit=100".format(image=image)

    tags = []
    tags_data = []
    manifest_data = []

    try:
        tag_rep = requests.get(url=tag_url)
        tag_req_json = tag_rep.json()
        manifest_data = tag_req_json['tags']
    except Exception as e:
        print('[Get tag Error]', e)
        return tags

    for manifest in manifest_data:
        name = manifest.get('name', '')

        # 排除 tag
        if is_exclude_tag(name):
            continue

        tags_data.append({
            'tag': name,
            'start_ts': manifest.get('start_ts')
        })

    tags_sort_data = sorted(tags_data, key=lambda i: i['start_ts'], reverse=True)

    # limit tag
    tags_limit_data = tags_sort_data[:limit]

    for t in tags_limit_data:
        tags.append(t['tag'])
    # image_aliyun_tags = get_repo_aliyun_tags(image)
    # for t in tags_limit_data:
    #     # 去除同步过的
    #     if t['tag'] in image_aliyun_tags:
    #         continue

    #     tags.append(t['tag'])

    # print('[repo tag]', tags)
    return tags


def get_repo_docker_tags(image, limit=5):
    """
    获取 docker.io repo 最新的 tag
    :param image:
    :param limit:
    :return:
    """
    tag_url = "https://registry.hub.docker.com/v2/repositories/{image}/tags?page_size={limit}".format(
        image=image, limit=limit)

    tags = []
    tags_data = []
    manifest_data = []

    try:
        tag_rep_text = requests.get(url=tag_url).text
        tag_req_json = json.loads(tag_rep_text)
    except Exception as e:
        print('[Get tag Error]', e)
        return tags

    for manifest in tag_req_json['results']:
        name = manifest.get('name', '')

        # 排除 tag
        if is_exclude_tag(name):
            continue

        tags_data.append({
            'tag': name,
            'last_updated': manifest.get('last_updated')
        })

    tags_sort_data = sorted(tags_data, key=lambda i: i['last_updated'], reverse=True)

    # limit tag
    tags_limit_data = tags_sort_data[:limit]

    for t in tags_limit_data:
        tags.append(t['tag'])
    # image_aliyun_tags = get_repo_aliyun_tags(image)
    # for t in tags_limit_data:
    #     # 去除同步过的
    #     if t['tag'] in image_aliyun_tags:
    #         continue

    #     tags.append(t['tag'])

    # print('[repo tag]', tags)
    return tags

def get_repo_elastic_tags(image, limit=5):
    """
    获取 elastic.io repo 最新的 tag
    :param image:
    :param limit:
    :return:
    """
    token_url = "https://docker-auth.elastic.co/auth?service=token-service&scope=repository:{image}:pull".format(
        image=image)
    tag_url = "https://docker.elastic.co/v2/{image}/tags/list".format(image=image)

    tags = []
    tags_data = []
    manifest_data = []

    hearders = {
        'User-Agent': 'docker/19.03.12 go/go1.13.10 git-commit/48a66213fe kernel/5.8.0-1.el7.elrepo.x86_64 os/linux arch/amd64 UpstreamClient(Docker-Client/19.03.12 \(linux\))'
    }

    try:
        token_res = requests.get(url=token_url, headers=hearders)
        token_data = token_res.json()
        access_token = token_data['token']
    except Exception as e:
        print('[Get repo token]', e)
        return tags

    hearders['Authorization'] = 'Bearer ' + access_token

    try:
        tag_rep = requests.get(url=tag_url, headers=hearders)
        tag_req_json = tag_rep.json()
        manifest_data = tag_req_json['tags']
    except Exception as e:
        print('[Get tag Error]', e)
        return tags

    for tag in manifest_data:
        # 排除 tag
        if is_exclude_tag(tag):
            continue
        tags_data.append(tag)

    tags_sort_data = sorted(tags_data, key=LooseVersion, reverse=True)

    # limit tag
    tags_limit_data = tags_sort_data[:limit]

    # image_aliyun_tags = get_repo_aliyun_tags(image)
    # for t in tags_limit_data:
    #     # 去除同步过的
    #     if t in image_aliyun_tags:
    #         continue

    #     tags.append(t)

    # print('[repo tag]', tags)
    return tags_limit_data


def get_repo_tags(repo, image, limit=5):
    """
    获取 repo 最新的 tag
    :param repo:
    :param image:
    :param limit:
    :return:
    """
    tags_data = []
    if repo == 'gcr.io':
        tags_data = get_repo_gcr_tags(image, limit, "gcr.io")
    elif repo == 'registry.k8s.io':
        tags_data = get_repo_gcr_tags(image, limit, "registry.k8s.io")
    elif repo == 'quay.io':
        tags_data = get_repo_quay_tags(image, limit)
    elif repo == 'docker.elastic.co':
        tags_data = get_repo_elastic_tags(image, limit)
    elif repo == 'docker.io':
        tags_data = get_repo_docker_tags(image, limit)
    return tags_data


def generate_dynamic_conf():
    """
    生成动态同步配置
    :return:
    """

    print('[generate_dynamic_conf] start.')
    config = None
    with open(CONFIG_FILE, 'r') as stream:
        try:
            config = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            print('[Get Config]', e)
            exit(1)

    print('[config]', config)

    skopeo_sync_data = {}

    for repo in config['images']:
        if repo not in skopeo_sync_data:
            skopeo_sync_data[repo] = {'images': {}}
        if config['images'][repo] is None:
            continue
        for image in config['images'][repo]:
            print("[image] {image}".format(image=image))
            sync_tags = get_repo_tags(repo, image, config['last'])
            if len(sync_tags) > 0:
                skopeo_sync_data[repo]['images'][image] = sync_tags
               # skopeo_sync_data[repo]['images'][image].append('latest')
            else:
                print('[{image}] no sync tag.'.format(image=image))

    print('[sync data]', skopeo_sync_data)

    with open(SYNC_FILE, 'w+') as f:
        yaml.safe_dump(skopeo_sync_data, f, default_flow_style=False)

    print('[generate_dynamic_conf] done.', end='\n\n')






generate_dynamic_conf()