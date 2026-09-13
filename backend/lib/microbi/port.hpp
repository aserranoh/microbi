#pragma once

#include <avr/io.h>
#include <stdint.h>

namespace microbi
{

    struct port
    {
        volatile uint8_t &port;
        volatile uint8_t &ddr;
        volatile uint8_t &pin;
    };

    constexpr port port_b{.port = PORTB, .ddr = DDRB, .pin = PINB};
    constexpr port port_c{.port = PORTC, .ddr = DDRC, .pin = PINC};
    constexpr port port_d{.port = PORTD, .ddr = DDRD, .pin = PIND};

} // namespace microbi