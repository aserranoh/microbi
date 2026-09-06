export type PortDirection = 'input' | 'output'
export type DataType = 'bool' | 'int8' | 'int16' | 'int32'

export interface Port {
    name: string
    direction: PortDirection
    data_type: DataType
}

export interface BaseConfigField {
    name: string
    default: unknown
}

export interface IntegerConfigField extends BaseConfigField {
    type: 'integer'
    default: number
    min: number | null
    max: number | null
}

export interface EnumConfigField extends BaseConfigField {
    type: 'enum'
    default: string
    choices: string[]
}

export type ConfigField = IntegerConfigField | EnumConfigField

export function isEnumField(f: ConfigField): f is EnumConfigField {
    return f.type === 'enum'
}

export function isIntegerField(f: ConfigField): f is IntegerConfigField {
    return f.type === 'integer'
}

export interface BlockType {
    name: string
    description: string
    ports: Port[]
    configuration: ConfigField[]
}

export interface Position {
    x: number
    y: number
}

export interface Block {
    id: string
    name: string
    block_type: string
    position: Position
    configuration: Record<string, unknown>
}

export interface PortReference {
    block_id: string
    port_name: string
}

export interface Connection {
    id: string
    source: PortReference
    target: PortReference
}

export interface Program {
    id: string
    name: string
    blocks: Block[]
    connections: Connection[]
}

export interface CodeGenerationError {
    block_type: string
    block_name: string
    block_uuid: string
    error_message: string
}

export interface CodeGenerationResult {
    code: string
    errors: CodeGenerationError[]
}
