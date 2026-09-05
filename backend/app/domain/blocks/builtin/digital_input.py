from app.domain.models import (
    Block,
    BlockCode,
    BlockType,
    BlockTypesRegistry,
    DataType,
    Port,
    PortDirection,
    Program,
    pin_configuration,
    port_configuration,
)


class DigitalInputImplementation:
    def generate_code(self, program: Program, block: Block) -> BlockCode:
        port = block.configuration["port"]
        pin = block.configuration["pin"]

        return BlockCode(
            include="<microbi/digital_input.hpp>",
            declaration=f"digital_input<port.{port}, {pin}> {block.name};",
            main_loop_body=f"{block.name}();",
        )


def init(registry: BlockTypesRegistry) -> None:
    registry.register(
        block_type=BlockType(
            name="Digital Input",
            description="A digital input block",
            ports=[
                Port(
                    name="value",
                    direction=PortDirection.OUTPUT,
                    data_type=DataType.BOOL,
                )
            ],
            configuration=[
                port_configuration(),
                pin_configuration(),
            ],
        ),
        implementation=DigitalInputImplementation(),
    )
