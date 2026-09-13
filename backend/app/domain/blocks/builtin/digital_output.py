from app.domain.models import (
    Block,
    BlockCodeGenerationError,
    BlockCodeGenerationResult,
    BlockType,
    BlockTypesRegistry,
    DataType,
    Port,
    PortDirection,
    PortReference,
    Program,
    pin_configuration,
    port_configuration,
)


class DigitalOutputImplementation:
    def generate_code(
        self,
        program: Program,
        block: Block,
    ) -> BlockCodeGenerationResult:
        port = f"port_{str(block.configuration['port']).lower()}"
        pin = block.configuration["pin"]
        src_port_ref = program.who_connects_to(
            PortReference(block_id=block.id, port_name="value"),
        )
        if src_port_ref is None:
            err_msg = "No source connected to the 'value' port"
            error = BlockCodeGenerationError.from_error_message(block, err_msg)
            return BlockCodeGenerationResult(block=block, errors=[error])
        src_block = program.get_block(src_port_ref.block_id)

        return BlockCodeGenerationResult(
            block=block,
            include="#include <microbi/digital_output.hpp>",
            declaration=f"digital_output<{port}, {pin}> {block.name};",
            main_loop_body=(
                f"{block.name}({src_block.name}.{src_port_ref.port_name});"
            ),
        )


def init(registry: BlockTypesRegistry) -> None:
    registry.register(
        block_type=BlockType(
            name="Digital Output",
            description="A digital output block",
            ports=(
                Port(
                    name="value",
                    direction=PortDirection.INPUT,
                    data_type=DataType.BOOL,
                ),
            ),
            configuration=(
                port_configuration(),
                pin_configuration(),
            ),
        ),
        implementation=DigitalOutputImplementation(),
    )
