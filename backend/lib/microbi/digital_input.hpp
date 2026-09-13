#pragma once

#include <stdint.h>

#include "port.hpp"

namespace microbi
{

    template <const port &dio_port, uint8_t dio_pin>
    class digital_input
    {
    public:
        bool value;

        inline digital_input()
        {
            // Configure the pin as an input
            dio_port.ddr &= ~_BV(dio_pin);
        }

        inline auto operator()() -> void
        {
            value = dio_port.pin & _BV(dio_pin);
        }
    };

} // namespace microbi