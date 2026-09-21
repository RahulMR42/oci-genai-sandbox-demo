# BYOC sandbox sample

This minimal image is a starting point for OCI GenAI Sandbox BYOC, which is currently limited availability. It contains Python 3.11 and the packages used by the package-and-model tutorial.

Build and test it locally:

```bash
docker build -t sandbox-tools:1.0 .
docker run --rm sandbox-tools:1.0
```

Push it to OCI Container Registry after authenticating Docker to your tenancy registry:

```bash
docker tag sandbox-tools:1.0 <region>.ocir.io/<tenancy-namespace>/<repository>/sandbox-tools:1.0
docker push <region>.ocir.io/<tenancy-namespace>/<repository>/sandbox-tools:1.0
```

Before using the image in a sandbox, scan and approve it according to your organization's image, IAM, and registry policies. Supply the resulting OCIR image URI through the Oracle-provided beta SDK BYOC configuration; the exact beta configuration field can change between preview releases.
