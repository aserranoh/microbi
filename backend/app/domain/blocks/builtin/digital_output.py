from app.domain.models import (
    Block,
    BlockCode,
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
    def generate_code(self, program: Program, block: Block) -> BlockCode:
        port = block.configuration["port"]
        pin = block.configuration["pin"]
        src_port_ref = program.who_connects_to(
            PortReference(block_id=block.id, port_name="value"),
        )
        if src_port_ref is None:
            err_msg = "No source connected to the 'value' port"
            return BlockCode(errors=[err_msg])
        src_block = program.get_block(src_port_ref.block_id)

        return BlockCode(
            include="<microbi/digital_output.hpp>",
            declaration=f"digital_output<port.{port}, {pin}> {block.name};",
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
