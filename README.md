# tracing-service

## ImmuDB

### Docker image UID and GID

- when running in k8s, check the UID and GID of the user in the docker image is you want to enable "runAsNonRoot"

```
    # Create a stopped container
    cid=$(podman create immudb:latest)

    # Copy the passwd file to your current host directory
    podman cp $cid:/etc/passwd /tmp/passwd

    # Read the file to find the user's UID
    grep immu /tmp/passwd 

    # Clean up the dummy container
    podman rm $cid
```