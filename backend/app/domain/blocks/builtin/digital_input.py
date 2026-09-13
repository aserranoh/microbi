from app.domain.models import (
    Block,
    BlockCodeGenerationResult,
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
    def generate_code(
        self,
        program: Program,
        block: Block,
    ) -> BlockCodeGenerationResult:
        port = f"port_{str(block.configuration['port']).lower()}"
        pin = block.configuration["pin"]

        return BlockCodeGenerationResult(
            block=block,
            include="#include <microbi/digital_input.hpp>",
            declaration=f"digital_input<{port}, {pin}> {block.name};",
            main_loop_body=f"{block.name}();",
        )


def init(registry: BlockTypesRegistry) -> None:
    registry.register(
        block_type=BlockType(
            name="Digital Input",
            description="A digital input block",
            ports=(
                Port(
                    name="value",
                    direction=PortDirection.OUTPUT,
                    data_type=DataType.BOOL,
                ),
            ),
            configuration=(
                port_configuration(),
                pin_configuration(),
            ),
        ),
        implementation=DigitalInputImplementation(),
    )
