# Rooms

<!-- Written from inventory/ and the runbooks by `python -m classroom_runbooks.inventory --write`: edit those, not this page. -->

The room inventory: each building's rooms and each room's equipment, linked to the
runbooks for that equipment. **The rooms are illustrative:** the buildings, rooms and
equipment are made up to resemble a large campus, not taken from any institution.

220 rooms in 10 buildings, 10,729 seats.

A room's identifier is its building's code and its room number: `ALD-104` is room 104
in Alder Hall. Quote it in tickets and handoff notes.

## Buildings

| Building | Code | Rooms | Seats |
| --- | --- | ---: | ---: |
| [Alder Hall](ald.md) | ALD | 28 | 1,155 |
| [Birch Science Center](bir.md) | BIR | 21 | 1,303 |
| [Cedar Hall](ced.md) | CED | 24 | 1,005 |
| [Elm Street Building](elm.md) | ELM | 25 | 840 |
| [Hawthorn Hall](haw.md) | HAW | 16 | 912 |
| [Laurel Library](lau.md) | LAU | 18 | 671 |
| [Maple Lecture Center](map.md) | MAP | 8 | 1,506 |
| [Oak Engineering Building](oak.md) | OAK | 24 | 923 |
| [Pine Learning Commons](pin.md) | PIN | 24 | 1,123 |
| [Willow Hall](wil.md) | WIL | 32 | 1,291 |

## Room types

Each room has its type's equipment unless its entry says otherwise.

| Type | Rooms | Seats | Fitted with |
| --- | ---: | --- | --- |
| Seminar room | 38 | 10–24 | Flat-panel display, Table HDMI and USB-C inputs, Wall button panel, Wireless presentation receiver, Wall network port ×2, Wi-Fi access point |
| Standard classroom | 84 | 25–65 | Laser projector, Motorized projection screen, Ceiling speakers, Audio processor and amplifier, Lectern HDMI and USB-C inputs, Presentation switcher, Wall button panel, Lectern network connection, Wall network port ×2, Wi-Fi access point, Document camera, Wireless keyboard and mouse, Lectern USB hub, Lectern computer |
| Hybrid classroom | 50 | 24–70 | Laser projector, Motorized projection screen, Confidence monitor, Ceiling speakers, Audio processor and amplifier, Ceiling microphone array, Lectern HDMI and USB-C inputs, Presentation switcher, Control processor and touch panel, Lectern network connection, Wall network port ×2, Wi-Fi access point, Document camera, Room webcam, Wireless keyboard and mouse, Lectern USB hub, Lectern computer |
| Lecture hall | 13 | 100–320 | Laser projector ×2, Motorized projection screen ×2, Confidence monitor, Ceiling speakers, Audio processor and amplifier, Lectern gooseneck microphone, Wireless handheld microphone ×2, Wireless lapel microphone, Assistive listening system, Lectern HDMI and USB-C inputs, HDBaseT video extender ×2, Presentation switcher, Control processor and touch panel, Lecture capture appliance and camera, Lectern network connection, Wall network port ×4, Wi-Fi access point ×3, Document camera, Wireless keyboard and mouse, Wireless presenter, Lectern USB hub, Lectern computer |
| Active learning classroom | 15 | 36–90 | Flat-panel display ×6, Interactive touch display, Ceiling speakers, Audio processor and amplifier, Wireless handheld microphone, Lectern HDMI and USB-C inputs, Table HDMI and USB-C inputs ×6, Presentation switcher, Control processor and touch panel, Wireless presentation receiver, Lectern network connection, Wall network port ×4, Wi-Fi access point ×2, Wireless keyboard and mouse, Lectern computer |
| Computer lab | 20 | 20–40 | Short-throw projector, Ceiling speakers, Audio processor and amplifier, Lectern HDMI and USB-C inputs, Presentation switcher, Wall button panel, Lectern network connection, Wall network port ×2, Room network switch, Wi-Fi access point, Wireless keyboard and mouse, Lectern computer, Student workstations (one set) |

## Equipment

| Equipment | Runbooks | Rooms with it | In all |
| --- | --- | ---: | ---: |
| Laser projector | [Projector shows no signal](../runbooks/av/rb-av-001-projector-shows-no-signal.md) (RB-AV-001); [Projector will not turn on](../runbooks/av/rb-av-002-projector-will-not-turn-on.md) (RB-AV-002); [Projected image is blurry, cut off or the wrong shape](../runbooks/av/rb-av-003-projected-image-is-blurry-cut-off-or-the-wrong.md) (RB-AV-003) | 147 | 160 |
| Short-throw projector | [Projector shows no signal](../runbooks/av/rb-av-001-projector-shows-no-signal.md) (RB-AV-001); [Projector will not turn on](../runbooks/av/rb-av-002-projector-will-not-turn-on.md) (RB-AV-002); [Projected image is blurry, cut off or the wrong shape](../runbooks/av/rb-av-003-projected-image-is-blurry-cut-off-or-the-wrong.md) (RB-AV-003) | 20 | 20 |
| Motorized projection screen | [Projected image is blurry, cut off or the wrong shape](../runbooks/av/rb-av-003-projected-image-is-blurry-cut-off-or-the-wrong.md) (RB-AV-003); [Projection screen will not come down or go up](../runbooks/av/rb-av-004-projection-screen-will-not-come-down-or-go-up.md) (RB-AV-004) | 147 | 160 |
| Flat-panel display | [Display shows no picture](../runbooks/av/rb-av-005-display-shows-no-picture.md) (RB-AV-005) | 53 | 146 |
| Interactive touch display | [Touch does not work on the interactive display](../runbooks/av/rb-av-006-touch-does-not-work-on-the-interactive-display.md) (RB-AV-006) | 14 | 14 |
| Confidence monitor | [Display shows no picture](../runbooks/av/rb-av-005-display-shows-no-picture.md) (RB-AV-005) | 62 | 62 |
| Ceiling speakers | [No sound from the room speakers](../runbooks/av/rb-av-007-no-sound-from-the-room-speakers.md) (RB-AV-007); [Speakers squeal or howl when a microphone is on](../runbooks/av/rb-av-010-speakers-squeal-or-howl-when-a-microphone-is-on.md) (RB-AV-010) | 182 | 182 |
| Audio processor and amplifier | [No sound from the room speakers](../runbooks/av/rb-av-007-no-sound-from-the-room-speakers.md) (RB-AV-007); [Microphone cannot be heard in the room](../runbooks/av/rb-av-008-microphone-cannot-be-heard-in-the-room.md) (RB-AV-008); [Remote participants cannot hear the room](../runbooks/av/rb-av-009-remote-participants-cannot-hear-the-room.md) (RB-AV-009); [Speakers squeal or howl when a microphone is on](../runbooks/av/rb-av-010-speakers-squeal-or-howl-when-a-microphone-is-on.md) (RB-AV-010) | 182 | 182 |
| Lectern gooseneck microphone | [Microphone cannot be heard in the room](../runbooks/av/rb-av-008-microphone-cannot-be-heard-in-the-room.md) (RB-AV-008); [Speakers squeal or howl when a microphone is on](../runbooks/av/rb-av-010-speakers-squeal-or-howl-when-a-microphone-is-on.md) (RB-AV-010) | 13 | 13 |
| Wireless handheld microphone | [Microphone cannot be heard in the room](../runbooks/av/rb-av-008-microphone-cannot-be-heard-in-the-room.md) (RB-AV-008); [Speakers squeal or howl when a microphone is on](../runbooks/av/rb-av-010-speakers-squeal-or-howl-when-a-microphone-is-on.md) (RB-AV-010) | 28 | 49 |
| Wireless lapel microphone | [Microphone cannot be heard in the room](../runbooks/av/rb-av-008-microphone-cannot-be-heard-in-the-room.md) (RB-AV-008); [Speakers squeal or howl when a microphone is on](../runbooks/av/rb-av-010-speakers-squeal-or-howl-when-a-microphone-is-on.md) (RB-AV-010) | 26 | 26 |
| Ceiling microphone array | [Remote participants cannot hear the room](../runbooks/av/rb-av-009-remote-participants-cannot-hear-the-room.md) (RB-AV-009) | 50 | 50 |
| Assistive listening system | [Assistive listening receiver is silent](../runbooks/av/rb-av-011-assistive-listening-receiver-is-silent.md) (RB-AV-011) | 17 | 17 |
| Lectern HDMI and USB-C inputs | [Laptop shows no picture through the HDMI or USB-C cable](../runbooks/av/rb-av-012-laptop-shows-no-picture-through-the-hdmi-or-usb-c.md) (RB-AV-012); [Picture flickers, sparkles or drops out](../runbooks/av/rb-av-013-picture-flickers-sparkles-or-drops-out.md) (RB-AV-013) | 182 | 182 |
| Table HDMI and USB-C inputs | [Laptop shows no picture through the HDMI or USB-C cable](../runbooks/av/rb-av-012-laptop-shows-no-picture-through-the-hdmi-or-usb-c.md) (RB-AV-012); [Picture flickers, sparkles or drops out](../runbooks/av/rb-av-013-picture-flickers-sparkles-or-drops-out.md) (RB-AV-013) | 53 | 146 |
| HDBaseT video extender | [Picture flickers, sparkles or drops out](../runbooks/av/rb-av-013-picture-flickers-sparkles-or-drops-out.md) (RB-AV-013) | 13 | 26 |
| Presentation switcher | [Projector shows no signal](../runbooks/av/rb-av-001-projector-shows-no-signal.md) (RB-AV-001) | 182 | 182 |
| Control processor and touch panel | [Touch panel or button panel does not respond](../runbooks/av/rb-av-014-touch-panel-or-button-panel-does-not-respond.md) (RB-AV-014) | 78 | 78 |
| Wall button panel | [Touch panel or button panel does not respond](../runbooks/av/rb-av-014-touch-panel-or-button-panel-does-not-respond.md) (RB-AV-014) | 142 | 142 |
| Wireless presentation receiver | [Cannot share a screen wirelessly](../runbooks/av/rb-av-015-cannot-share-a-screen-wirelessly.md) (RB-AV-015) | 58 | 58 |
| Lecture capture appliance and camera | [A class was not recorded by lecture capture](../runbooks/av/rb-av-016-a-class-was-not-recorded-by-lecture-capture.md) (RB-AV-016) | 13 | 13 |
| Lectern network connection | [Network](../runbooks/network/index.md) | 182 | 182 |
| Wall network port | [Network](../runbooks/network/index.md) | 220 | 508 |
| Room network switch | [Network](../runbooks/network/index.md) | 20 | 20 |
| Wi-Fi access point | [Network](../runbooks/network/index.md) | 218 | 259 |
| Document camera | [Peripherals](../runbooks/peripherals/index.md) | 138 | 138 |
| Room webcam | [Peripherals](../runbooks/peripherals/index.md) | 56 | 56 |
| Wireless keyboard and mouse | [Peripherals](../runbooks/peripherals/index.md) | 182 | 182 |
| Wireless presenter | [Peripherals](../runbooks/peripherals/index.md) | 16 | 16 |
| Lectern USB hub | [Peripherals](../runbooks/peripherals/index.md) | 141 | 141 |
| Lectern computer | [Account access](../runbooks/accounts/index.md) | 182 | 182 |
| Student workstations (one set) | [Account access](../runbooks/accounts/index.md) | 20 | 20 |
