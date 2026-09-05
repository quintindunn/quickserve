from QuickServeDriver.services.base_service import BaseService

if __name__ == "__main__":
    from QuickServeFS import config

    service = BaseService(
        cfg=config,
        service_name="Minecraft1.8.9",
        module=config.resolver.modules.get("Minecraft"),
    )
    print(service.working_directory())
