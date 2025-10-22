from model.Decoder_Dino import DecoderV1
from model.Decoder_Slips_v11 import DecoderV1_1
from model.Decoder_Slips_v12 import DecoderV1_2

Decoder_map = {
    'Dino_Only': DecoderV1,
    'Slips_Only_v11': DecoderV1_1,
    'Slips_Only_v12': DecoderV1_2,
}
