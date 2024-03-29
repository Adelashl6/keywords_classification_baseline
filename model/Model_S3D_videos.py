''' Define the Transformer model '''
from utils.utils import *
from model.Decoder import Decoder
#from model.EncoderRNN import EncoderRNN
#from model.c3d import *
#from model.s3d import *

__author__ = 'Jacob Zhiyuan Fang'


class Model(nn.Module):
    ''' A sequence to sequence model with attention mechanism. '''

    def __init__(
            self,
            n_cap_vocab, cap_max_seq, dim_language = 768,
            d_word_vec=512, d_model=512, d_inner=2048,
            n_layers=6, n_head=8, d_k=64, d_v=64, dropout=0.1,
            c3d_path=False, tgt_emb_prj_weight_sharing=True):

        super().__init__()

        # Load Kinetics/Self pre-trained C3D model, return only features
        self.encoder = nn.Linear(1024, 768)

        self.decoder = Decoder(
            n_tgt_vocab=n_cap_vocab, len_max_seq=cap_max_seq,
            d_word_vec=d_word_vec, d_model=d_model, d_inner=d_inner,
            n_layers=n_layers, n_head=n_head, d_k=d_k, d_v=d_v,
            dropout=dropout)

        self.cap_word_prj = nn.Linear(d_model, n_cap_vocab, bias=False)

        nn.init.xavier_normal_(self.cap_word_prj.weight)

        assert d_model == d_word_vec, \
            'To facilitate the residual connections, ' \
            'the dimensions of all module outputs shall be the same.'

        if tgt_emb_prj_weight_sharing:
            # Share the weight matrix between target word embedding & the final logit dense layer
            self.cap_word_prj.weight = self.decoder.tgt_word_emb.weight
            self.x_logit_scale = (d_model ** -0.5)
        else:
            self.x_logit_scale = 1.

    def forward(self, vis_feat, video_len, tgt_seq, tgt_pos):

        tgt_seq, tgt_pos = tgt_seq[:, :-1], tgt_pos[:, :-1]
        enc_output = self.encoder(vis_feat)

        # Feed video in C3D model sequentially, now only support recurrent handle
        dec_output, *_ = self.decoder(tgt_seq, tgt_pos, enc_output)
        seq_logit = self.cap_word_prj(dec_output) * self.x_logit_scale

        return seq_logit.view(-1, seq_logit.size(2))

