#pragma once

#include <stdint.h>

#include "port.hpp"

namespace microbi
{

    template <const port &dio_port, uint8_t dio_pin>
    class digital_output
    {
    public:
        inline digital_output()
        {
            // Configure the pin as an output
            dio_port.ddr |= _BV(dio_pin);
        }

        inline auto operator()(bool value) -> void
        {
            if (value)
            {
                dio_port.port |= _BV(dio_pin);
            }
            else
            {
                dio_port.port &= ~_BV(dio_pin);
            }
        }
    };

} // namespace microbi