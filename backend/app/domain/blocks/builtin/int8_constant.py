from app.domain.models import (
    Block,
    BlockCode,
    BlockType,
    BlockTypesRegistry,
    DataType,
    IntegerConfiguration,
    Port,
    PortDirection,
    Program,
)


class Int8ConstantImplementation:
    def generate_code(self, program: Program, block: Block) -> BlockCode:
        const_value = block.configuration["value"]

        return BlockCode(
            include="<microbi/int8_constant.hpp>",
            declaration=f"int8_constant<{const_value}> {block.name};",
        )


def init(registry: BlockTypesRegistry) -> None:
    registry.register(
        block_type=BlockType(
            name="Int8 Constant",
            description="An 8-bit integer constant block",
            ports=(
                Port(
                    name="value",
                    direction=PortDirection.OUTPUT,
                    data_type=DataType.INT8,
                ),
            ),
            configuration=(
                IntegerConfiguration(
                    name="value",
                    default=0,
                    min=-128,
                    max=127,
                ),
            ),
        ),
        implementation=Int8ConstantImplementation(),
    )
